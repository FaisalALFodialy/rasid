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
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, WebDriverException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playwright.sync_api import sync_playwright

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
    def __init__(self, category_id=8):
        self.category_id = category_id
        self.base_url = "https://tenders.etimad.sa/Tender/AllTendersForVisitor"
        self.params = {
            "MultipleSearch": "",
            "TenderCategory": "",
            "TenderActivityId": self.category_id,
            "ReferenceNumber": "",
            "TenderNumber": "",
            "agency": "",
            "ConditionaBookletRange": "",
            "PublishDateId": 5,
            "IsSearch": "true",
            "PageNumber": 1
        }
        self.data = []
        
    def scrape_tenders(self, max_pages=3):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        for page in range(1, max_pages + 1):
            self.params["PageNumber"] = page
            print(f"📄 Fetching page {page}...")

            response = requests.get(self.base_url, params=self.params, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")

            cards = soup.find_all("div", class_="tender-card")
            if not cards:
                print("⚠️ No tenders found.")
                break

            for card in cards:
                try:
                    deadline = card.find("div").find("span").text.strip()
                    title = card.find("h3").find("a").text.strip()
                    gov_desc = card.find("div").find("p").text.strip()
                    type_tag = card.select_one("label.ml-3 + span")
                    activity_type = type_tag.text.strip() if type_tag else "N/A"

                    self.data.append({
                        "Title": title,
                        "Government Description": gov_desc,
                        "Activity Type": activity_type,
                        "Date": deadline
                    })
                except Exception as e:
                    print("❌ Error parsing card:", e)

        print("✅ Scraping complete.")
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
        scraper = TenderScraper(category_id=CATEGORY_ID_MAP.get(self.category, 9))
        data = scraper.scrape_tenders()
        report = ExcelReportGenerator(data)
        file = report.generate_excel()
        sender = EmailSender(self.sender_email, self.password, self.receiver_emails)
        sender.send_email(file)
