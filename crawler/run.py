import re
from playwright.sync_api import sync_playwright
import time

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

def parse_detail_page(page, url):
    """
    상세 페이지 하나에서 정보 추출
    상세 페이지에서 회사 이름, 포지션 등등 추출하는 함수
    """
    page.goto(BASE_URL + url)

    # 7. 제목(h1)이 나타날 때까지 기다리기
    title = page.wait_for_selector('h1')
    # 8. h1에서 title 텍스트 추출
    title = title.inner_text()

    # 회사 이름 추출하기
    company_name = page.locator('a.name').inner_text()

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

    # 11. 자격요건 추출하기
    qual_dt = page.locator("dt:has-text('자격요건')")
    qual_dl = qual_dt.locator("xpath=ancestor::dl[1]")
    qual_text = qual_dl.locator("dd pre").inner_text()

    # 12. 우대사항 추출하기
    prefer_dt = page.locator("dt:has-text('우대사항')")
    prefer_dl = prefer_dt.locator("xpath=ancestor::dl[1]")
    prefer_text = prefer_dl.locator("dd pre").inner_text()

    # 13. 복지 및 혜택 추출하기
    benefit_dt = page.locator("dt:has-text('복지 및 혜택')")
    benefit_dl = benefit_dt.locator("xpath=ancestor::dl[1]")
    benefit_text = benefit_dl.locator("dd pre").inner_text()

    # 14. 채용절차 및 기타 지원 유의사항 추출하기
    process_dt = page.locator("dt:has-text('채용절차 및 기타 지원 유의사항')")
    process_dl = process_dt.locator("xpath=ancestor::dl[1]")
    process_text = process_dl.locator("dd pre").inner_text()

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

        detail_urls = collect_detail_urls(page)
        print(len(detail_urls))

        for url in detail_urls[:1]:
            item = parse_detail_page(page, url)
            print(item)


if __name__ == "__main__":
    main()