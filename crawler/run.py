import re
from playwright.sync_api import sync_playwright
import csv

BASE_URL = "https://jumpit.saramin.co.kr"
LIST_URL = "https://jumpit.saramin.co.kr/positions?jobCategory=8&sort=popular"


def collect_detail_urls(page):
    """
    목록 페이지에서 상세 페이지 URL들을 모아서 반환함
    return: list[str]

    이 함수는 '/position/'이 포함된 모든 링크들을 찾아서 리스트로 반환해준다.
    우리가 관심있는 상세 페이지 링크들은 모두 '/position/'이 포함되어 있기 때문에!!!
    """
    detail_urls = []
    #4. '/position/'가 들어간 링크들을 찾는 locator 정의
    locator = page.locator("a[href*='/position/']")
    #5. locator로부터 href 속성들 전부 가져오기
    hrefs_count = locator.count()
    for i in range(hrefs_count):
        href = locator.nth(i).get_attribute("href")
        # print(href)
        #6. 중복 제거 + None 제거
        if href is not None:
            detail_urls.append(href)
    detail_urls = list(set(detail_urls))

    return detail_urls

def safe_inner_text(locator, default=""):
    '''
    locator에서 inner_text를 안전하게 추출하는 함수
    만약 해당 locator가 없으면 default 값을 반환
    '''
    if locator.count() == 0:
        return default
    return locator.first.inner_text().strip()

def parse_detail_page(page, url):
    """
    상세 페이지 하나에서 정보 추출
    상세 페이지에서 회사 이름, 포지션 등등 추출하는 함수
    """
    page.goto(BASE_URL + url)

    # 7. 제목(h1)이 나타날 때까지 기다리기
    title = page.wait_for_selector('h1')
    # 8. h1에서 title 텍스트 추출
    title = safe_inner_text(page.locator('h1'))

    # 회사 이름 추출하기
    company_name = safe_inner_text(page.locator('a.name'))

    # 9. 기술스택 추출하기
    tech_dt = page.locator('dt:has-text("기술스택")')
    dl = tech_dt.locator("xpath=ancestor::dl[1]")
    imgs = dl.locator("img[alt]")
    # print(imgs.count()) # 기술스택 이미지 개수 출력

    tech_stack = []
    for i in range(imgs.count()):
        tech_stack.append(imgs.nth(i).get_attribute("alt"))
    print(tech_stack)
    
    # 10. 주요업무 추출하기
    work_dt = page.locator("dt:has-text('주요업무')")
    work_dl = work_dt.locator("xpath=ancestor::dl[1]")
    work_text = work_dl.locator("dd pre").inner_text()
    work_text = safe_inner_text(work_dl.locator("dd pre"))

    # 11. 자격요건 추출하기
    qual_dt = page.locator("dt:has-text('자격요건')")
    qual_dl = qual_dt.locator("xpath=ancestor::dl[1]")
    qual_text = safe_inner_text(qual_dl.locator("dd pre"))

    # 12. 우대사항 추출하기
    prefer_dt = page.locator("dt:has-text('우대사항')")
    prefer_dl = prefer_dt.locator("xpath=ancestor::dl[1]")
    prefer_text = safe_inner_text(prefer_dl.locator("dd pre"))

    # 13. 복지 및 혜택 추출하기
    benefit_dt = page.locator("dt:has-text('복지 및 혜택')")
    benefit_dl = benefit_dt.locator("xpath=ancestor::dl[1]")
    benefit_text = safe_inner_text(benefit_dl.locator("dd pre"))

    # 14. 채용절차 및 기타 지원 유의사항 추출하기
    process_dt = page.locator("dt:has-text('채용절차 및 기타 지원 유의사항')")
    if process_dt.count() > 0:
        process_dl = process_dt.locator("xpath=ancestor::dl[1]")
        process_text = safe_inner_text(process_dl.locator("dd pre"))
    else:
        process_text = ""

    # 15. 아이템 딕셔너리로 정리하기
    item = {
        "url": BASE_URL + url,
        "title": title,
        "company_name": company_name,
        "tech_stack": tech_stack,
        "work": work_text,
        "qualification": qual_text,
        "prefer": prefer_text,
        "benefit": benefit_text,
        "process": process_text,
    }

    return item

def scroll_down(page):
    """
    페이지를 아래로 스크롤하는 함수
    동작원리 초기 카드 숫자에서 계속 카드를 추가하는데 더 이상 카드가 추가되지 않으면
    페이지가 끝났다고 판단함.

    이 루프를 3번 반복해도 변화가 없으면 페이지가 진짜 끝났다고 간주
    """
    card_links = page.locator("a[href*='/position/']")

    stable_rounds = 0 # 전체 카드 카운트 루프 초기에는 0으로 세팅
    prev_count = 0 # 이전 카드 개수

    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)") # 페이지 맨 아래로 스크롤
        page.wait_for_timeout(1200) # 1.2초 대기 / 스크롤 후 로딩 시간 주기 위함

        current_count = card_links.count() # 현재 카드 개수
        print(f"현재 카드 갯수: {current_count}")

        if current_count == prev_count:
            stable_rounds += 1 # 현재 카드 개수와 이전 카드 개수가 같으면 라운드 수를 하나 증가시킴
        else:
            stable_rounds = 0 # 카드 개수가 변화가 있으면 전체 라운드 수를 0으로 초기화 시킴
            prev_count = current_count # 이전 카드 개수를 현재 카드 개수로 업데이트! 그래야지 다음 루프에서 비교 가능하기 때문!
        
        if stable_rounds >= 3:
            break # 3번 연속으로 카드 개수가 변화가 없으면 종료

def save_items_to_csv(items, output_path="data/jumpit_jobs.csv"):
    if not items:
        print("저장할 데이터가 없습니다.")
        return
    
    fieldnames = [
        'url',
        'title',
        'company_name',
        'tech_stack',
        'work',
        'qualification',
        'prefer',
        'benefit',
        'process',
    ]

    with open(output_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            row = item.copy()
            row["tech_stack"] = ", ".join(item["tech_stack"])
            writer.writerow(row)
    
    print(f"CSV 저장: {output_path} ({len(items)})개 항목")



def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(LIST_URL)

        # 1. 카드들이 로딩됐다는 기준이 되는 요소 기다리기
        element = page.wait_for_selector('img') # 카드 이미지 태그 로딩될 때까지 대기하기
        # 2. 카드(또는 상세 링크) locator 만들기
        cards = page.locator("div.img_box") # 카드 전체를 나타내는 앵커 태그 선택자
        # 3. 카드 개수 출력하기
        print(f"Number of cards found: {cards.count()}")
        
        # 스크롤 다운 함수 호출
        scroll_down(page)

        # 상세 페이지 URL들 수집
        detail_urls = collect_detail_urls(page)
        print(len(detail_urls))

        # 상세 페이지 파싱
        items = []

        for url in detail_urls: #for url in detail_urls[:5]: # 테스트용으로 5개만 크롤링
            item = parse_detail_page(page, url)
            items.append(item)
        
        save_items_to_csv(items, "data/jumpit_jobs.csv") # CSV로 저장하기

        browser.close()


if __name__ == "__main__":
    main()