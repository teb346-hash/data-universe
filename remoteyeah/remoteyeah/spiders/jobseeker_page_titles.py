import re
import scrapy
from typing import Iterable
import json
from plyer import notification
from multiprocessing import Process
from scrapy.utils.reactor import install_reactor
install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
from twisted.internet import reactor

def show_notification(title, posted_on):
    notification.notify(
        title="New Job Listing",
        message=f"This is first new one. \n Title : {title} \n Posted on : {posted_on}",
        timeout=86400
    )

        
def load_existing_data(filename="./history.json"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            print("history.json exists.")
            return json.load(file)
    except FileNotFoundError:
        print("No history.")
        return []
def save_data(filename="./history.json", data=[]):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            print("writting history.")

            json.dump(data, file, indent=4, ensure_ascii=False)
    except Exception as e:

        print(f"Error saving file {filename}: {e}")

def add_new_data(new_data, existing_data):

    existing_urls = {entry['url'] for entry in existing_data}  
    new_entries = [entry for entry in new_data if entry['url'] not in existing_urls]  

    if new_entries:
        existing_data.extend(new_entries)
    return existing_data


class JobseekerSpider(scrapy.Spider):
    """
      # 1~5 pages
      scrapy crawl jobseeker -a pages=1-5 -O titles.jsonl

      # 1,3,7 pages
      scrapy crawl jobseeker -a pages=1,3,7 -O titles.csv

      # start/end 
      scrapy crawl jobseeker -a start=2 -a end=4 -O p2to4.json
    """
    name = "jobseeker"
    allowed_domains = ["remoteyeah.com"]
    def __init__(self, pages: str | None = None, start: int | None = None, end: int | None = None, \
             follow: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.follow_detail = bool(int(follow))
        self.new_data = []  


        self.existing_data = load_existing_data() 
        targets: list[int] = []
        if pages:
            pages = pages.strip()
            if "-" in pages:
                a, b = pages.split("-", 1)
                a, b = int(a), int(b)
                if a > b:
                    a, b = b, a
                targets = list(range(a, b + 1))
            else:
                targets = [int(x) for x in pages.split(",") if x.strip().isdigit()]
        elif start is not None or end is not None:
            s = int(start or 1)
            e = int(end or s)
            if s > e:
                s, e = e, s
            targets = list(range(s, e + 1))
        else:
            targets = [1]

        seen = set()
        self.target_pages: list[int] = []
        for p in targets:
            if p >= 1 and p not in seen:
                seen.add(p)
                self.target_pages.append(p)

        if not self.target_pages:
            self.target_pages = [1]
        self._page_url_template: str | None = None

    def start_requests(self):
        yield scrapy.Request("https://remoteyeah.com/", callback=self.parse_home, dont_filter=True)

    def parse_home(self, response):
        hrefs = response.css("a::attr(href)").getall()
        template = self._detect_pagination_template(hrefs)
        self._page_url_template = template 


        for p in self.target_pages:
            if template:
                url = self._build_from_template(response, template, p)
                yield scrapy.Request(url, callback=self.parse_list, cb_kwargs={"page": p}, dont_filter=True)
            else:
                candidates = [
                    f"https://remoteyeah.com/?page={p}",
                    f"https://remoteyeah.com/remote-jobs?page={p}",
                    f"https://remoteyeah.com/jobs?page={p}",
                    f"https://remoteyeah.com/page/{p}",
                ]
                for u in candidates:
                    yield scrapy.Request(u, callback=self.parse_list, cb_kwargs={"page": p}, dont_filter=True)

    def _detect_pagination_template(self, hrefs: Iterable[str]):

        for h in hrefs:
            if not h:
                continue
            m = re.search(r"([?&]page=)(\d+)", h)
            if m:
                return re.sub(r"([?&]page=)\d+", r"\1{page}", h)
            m = re.search(r"(/page/)(\d+)", h)
            if m:
                return re.sub(r"(/page/)\d+", r"\1{page}", h)
        return None

    def _build_from_template(self, response, template: str, page: int):
        if "{page}" in template:
            return response.urljoin(template.replace("{page}", str(page)))
        return response.urljoin(template)


    def parse_detail(self, response, page: int, title: str, company: str, skills: list[str], url: str):
  
        description_items = response.css('div.rich-text h2:contains("Description:") + ul li::text').getall()
        description = [item.strip() for item in description_items if item.strip()]  

        requirements_items = response.css('div.rich-text h2:contains("Requirements:") + ul li::text').getall()
        requirements = [item.strip() for item in requirements_items if item.strip()]  
        
        about_section = response.css('div.box-title:contains("About the job")')

        job_details = {}
        if about_section:
      
            about_section_content = about_section.xpath("following::div[contains(@class, 'box-content')][1]")

       
            location_tags = about_section_content.xpath(".//span[contains(text(), 'Location requirements')]/following-sibling::div//a/span[not(text()='🌍')]/text()").getall()
            
            job_details["location"] = [(location.strip()) for location in location_tags]
            
            job_details["posted_on"] = about_section_content.xpath(".//span[contains(text(), 'Posted on')]/following-sibling::p/text()").get(default="").strip()
            job_details["job_type"] = about_section_content.xpath(".//span[contains(text(), 'Job type')]/following-sibling::div/a/text()").get(default="").strip()
            job_details["salary"] = about_section_content.xpath(".//span[contains(text(), 'Salary')]/following-sibling::div/div/text()").get(default="").strip()
            job_details["experience_level"] = about_section_content.xpath(".//span[contains(text(), 'Experience level')]/following-sibling::div/a/text()").get(default="").strip()
            job_details["degree_requirement"] = about_section_content.xpath(".//span[contains(text(), 'Degree requirement')]/following-sibling::div/a/text()").get(default="").strip()

        
        new_job = {
            "page": page,
            "title": title,
            "company": company,
            "skills": skills,
            "url": url,
            "posted_on": job_details.get("posted_on", ""),
            "job_type": job_details.get("job_type", ""),
            "salary": job_details.get("salary", ""),
            "location": job_details.get("location", []),
            "experience_level": job_details.get("experience_level", ""),
            "degree_requirement": job_details.get("degree_requirement", ""),
            "description": description,
            "requirements": requirements
        }
        self.new_data.append(new_job)
        print("processing page with new job:", page, " : ", title)


    def parse_list(self, response, page: int):
        job_links = response.css('a[href*="/jobs/"]')

        for a in job_links:
            title = a.css("::text").get(default="").strip()
            if not title or len(title.split()) < 2:
                continue
            url = response.urljoin(a.attrib.get("href", ""))
       
            if any(job['url'] == url for job in self.existing_data):  
                continue  
            card = a.xpath("ancestor::article[1]")
            if not card:

                card = a.xpath("ancestor::li[1]") or a.xpath("ancestor::div[contains(@class,'job')][1]")

            company = card.css(".job-company::text").get(default="").strip()
            if not company:
                company = card.css("h3::text").get(default="").strip()


            skill_selectors = [
                'a[href*="-jobs"]::text',
                ".skills a::text",
                ".tags a::text",
                ".tag::text",
                ".chip::text",
            ]

            skills = []
            for sel in skill_selectors:
                skills.extend([t.strip() for t in card.css(sel).getall() if t and t.strip()])

            blacklist = {"apply now"}
            cleaned = []
            seen = set()
            for s in skills:
                ss = s.strip()
                if not ss or ss.lower() in blacklist:
                    continue
                if len(ss) < 2:
                    continue
                if ss not in seen:
                    seen.add(ss)
                    cleaned.append(ss)

            yield response.follow(
                url,
                callback=self.parse_detail,
                cb_kwargs={"page": page, "title": title, "company": company, "skills": cleaned, "url": url},
                dont_filter=True,
            )

        if not job_links:
            self.logger.warning("No job links on %s ; check selector.", response.url)
            
    def closed(self, reason):
        try:
            print(f"Spider closed. Reason: {reason}")          

            if self.new_data:
    
                updated_data = add_new_data(self.new_data, self.existing_data) 
                save_data(data=updated_data) 
                print("new jobs : ", [job["title"] for job in self.new_data])

                first_job = self.new_data[0]
                notification_process = Process(target=show_notification, args=(first_job["title"], first_job["posted_on"]))

                notification_process.start()
                print("Main process ends, but notification process continues.")
                return
        except Exception as e:
            print(f"Error during closing: {e}")