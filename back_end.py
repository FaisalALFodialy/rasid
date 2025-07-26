import time
import os
import smtplib
import ssl
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ✅ Category mapping
CATEGORY_ID_MAP = {
    "Trade": 1,
    "Contracting": 2,
    "Operation, maintenance, and cleaning of facilities": 3,
    "Real estate and land": 4,
    "Industry, mining, and recycling": 5,
    "Gas, water, and energy": 6,
    "Mines, petroleum, and quarries": 7,
    "Media, publishing, and distribution": 8,
    "Communications and Information Technology": 9,
    "Agriculture and Fishing": 10,
    "Healthcare and Rehabilitation": 11,
    "Education and Training": 12,
    "Employment and Recruitment": 13,
    "Security and Safety": 14,
    "Transportation, Mailing and Storage": 15,
    "Consulting Professions": 16,
    "Tourism, Restaurants, Hotels and Exhibition Organization": 17,
    "Finance, Financing and Insurance": 18
}

class TenderScraper:
    def __init__(self, category):
        self.activity_id = CATEGORY_ID_MAP.get(category)
        if self.activity_id is None:
            raise ValueError(f"Invalid category: {category}")

        self.base_url = (
            f"https://tenders.etimad.sa/Tender/AllTendersForVisitor?"
            f"&MultipleSearch=&TenderCategory=&TenderActivityId={self.activity_id}"
            f"&ReferenceNumber=&TenderNumber=&agency=&ConditionaBookletRange=&PublishDateId=5"
        )
        self.data = []

    class TenderScraper:
    def scrape_tenders(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = "/usr/bin/chromium-browser"

        service = Service("/usr/bin/chromedriver")  # use system driver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get("https://tenders.etimad.sa/Tender/AllTendersForVisitor")  # test load
        print("✅ Browser loaded successfully.")
        driver.quit()
        time.sleep(4)

        page_count = 0
        while page_count < max_pages:
            print(f"Scraping page {page_count + 1}...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.find_all('div', class_='tender-card')

            for card in cards:
                try:
                    date = card.find('div').find('span') if card.find('div') else None
                    deadline = date.text.strip() if date else "N/A"

                    title_tag = card.find('h3').find('a') if card.find('h3') else None
                    title = title_tag.text.strip() if title_tag else "N/A"

                    gov_desc_tag = card.find('div').find('p') if card.find('div') else None
                    gov_desc = gov_desc_tag.text.strip() if gov_desc_tag else "N/A"

                    type_tag = card.select_one('label.ml-3 + span')
                    activity_type = type_tag.text.strip() if type_tag else "N/A"

                    self.data.append({
                        'Title': title,
                        'Government Description': gov_desc,
                        'Activity Type': activity_type,
                        'Date': deadline
                    })
                except Exception as e:
                    print(f"Error on card in page {page_count + 1}: {e}")

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button.page-link[aria-label='Next']")
                if "disabled" in next_button.get_attribute("class").lower():
                    print("Next button is disabled. Reached last page.")
                    break
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
                page_count += 1
            except (NoSuchElementException, ElementClickInterceptedException):
                print("Next button not found or clickable. Ending pagination.")
                break

        driver.quit()
        print("Scraping complete.")
        return self.data

class ExcelReportGenerator:
    def __init__(self, data, filename="rasid_tenders_report.xlsx"):
        self.data = data
        self.filename = filename

    def generate_excel(self):
        df = pd.DataFrame(self.data)
        df.to_excel(self.filename, index=False)
        print(f"Excel Report saved as {self.filename}")
        return self.filename

class EmailSender:
    def __init__(self, sender_email, password, receiver_emails):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = sender_email
        self.password = password
        self.receiver_emails = receiver_emails

    def send_email(self, attachment_filename):
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(self.receiver_emails)
        msg["Subject"] = f"Rasid Tenders Report - {datetime.date.today()}"

        body = "Hello,\n\nPlease find the attached Rasid tender opportunities report.\n\nRegards."
        msg.attach(MIMEText(body, "plain"))

        with open(attachment_filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={attachment_filename}")
            msg.attach(part)

        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=context)
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_emails, msg.as_string())
            server.quit()
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")
        os.remove(attachment_filename)

class RasidJob:
    def __init__(self, sender_email, password, receiver_emails, category):
        self.sender_email = sender_email
        self.password = password
        self.receiver_emails = receiver_emails
        self.category = category

    def run(self):
        print("📦 Running Rasid job...")
        scraper = TenderScraper(self.category)
        data = scraper.scrape_tenders()
        report = ExcelReportGenerator(data)
        file = report.generate_excel()
        sender = EmailSender(self.sender_email, self.password, self.receiver_emails)
        sender.send_email(file)
