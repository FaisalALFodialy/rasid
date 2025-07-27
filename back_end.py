import time
import os
import smtplib
import ssl
import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Category mapping
CATEGORY_ID_MAP = {
    "Trade": 1, "Contracting": 2, "Operation, maintenance, and cleaning of facilities": 3,
    "Real estate and land": 4, "Industry, mining, and recycling": 5, "Gas, water, and energy": 6,
    "Mines, petroleum, and quarries": 7, "Media, publishing, and distribution": 8,
    "Communications and Information Technology": 9, "Agriculture and Fishing": 10,
    "Healthcare and Rehabilitation": 11, "Education and Training": 12,
    "Employment and Recruitment": 13, "Security and Safety": 14,
    "Transportation, Mailing and Storage": 15, "Consulting Professions": 16,
    "Tourism, Restaurants, Hotels and Exhibition Organization": 17,
    "Finance, Financing and Insurance": 18
}

class TenderScraper:
    def __init__(self, category_id=8):
        self.category_id = category_id
        self.base_url = "https://tenders.etimad.sa/Tender/AllTendersForVisitor"
        self.params = {
            "TenderActivityId": self.category_id,
            "PublishDateId": 5,
            "IsSearch": "true",
            "PageNumber": 1
        }
        self.data = []

    def scrape_tenders(self, max_pages=3):
        headers = {"User-Agent": "Mozilla/5.0"}
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
        print(f"📁 Excel saved as {self.filename}")
        return self.filename


class EmailSender:
    def __init__(self, sender_email, password):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = sender_email
        self.password = password

     def send_to_admin(self, report_file, client_email, category, time_of_day, frequency):
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = "faisal8883003@hotmail.com"
        msg["Subject"] = f"📊 Rasid Report Request - {datetime.date.today()}"

        body = f"""
Hello Faisal,

A new client has requested Rasid tender reports.

📧 Client Email: {client_email}
📂 Category: {category}
🕒 Preferred Time: {time_of_day}
📆 Frequency: {frequency}

The attached file contains the current tenders.

Regards,  
Rasid System Bot
"""
        msg.attach(MIMEText(body, "plain"))

        with open(report_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={report_file}")
            msg.attach(part)

        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=context)
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, ["faisal8883003@hotmail.com"], msg.as_string())
            server.quit()
            print("📧 Email sent to admin!")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
        os.remove(report_file)


class RasidJob:
    def __init__(self, sender_email, password, client_email, category, time_of_day, frequency):
        self.sender_email = sender_email
        self.password = password
        self.client_email = client_email
        self.category = category
        self.time_of_day = time_of_day
        self.frequency = frequency

    def run(self):
        print("🚀 Running RasidJob...")
        category_id = CATEGORY_ID_MAP.get(self.category, 9)
        scraper = TenderScraper(category_id=category_id)
        data = scraper.scrape_tenders()
        report = ExcelReportGenerator(data)
        file = report.generate_excel()
        mailer = EmailSender(self.sender_email, self.password)
        mailer.send_to_admin(file, self.client_email, self.category, self.time_of_day, self.frequency)

