import time
import os
import smtplib
import ssl
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (NoSuchElementException, 
                                      ElementClickInterceptedException,
                                      WebDriverException)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping from category name to TenderActivityId
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

    def _init_driver(self):
        """Initialize and return a Chrome WebDriver with proper configuration"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            # Use webdriver_manager to handle driver installation
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize ChromeDriver: {str(e)}")
            raise ValueError("Failed to initialize web browser. Please try again later.")

    def scrape_tenders(self, max_pages=2):
        """Scrape tenders with proper error handling and resource management"""
        driver = None
        try:
            driver = self._init_driver()
            driver.get(self.base_url + "1")
            time.sleep(4)  # Allow page to load

            page_count = 0
            while page_count < max_pages:
                logger.info(f"Scraping page {page_count + 1}...")
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
                            'Date': deadline,
                            'Category ID': self.activity_id
                        })
                    except Exception as e:
                        logger.warning(f"Error processing card: {str(e)}")
                        continue

                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "button.page-link[aria-label='Next']")
                    if "disabled" in next_button.get_attribute("class").lower():
                        logger.info("Reached last page of results.")
                        break
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)  # Wait for next page to load
                    page_count += 1
                except (NoSuchElementException, ElementClickInterceptedException):
                    logger.info("No more pages available.")
                    break

            if not self.data:
                logger.warning("No tender data was scraped.")
                raise ValueError("No tenders found for the selected category.")

            return self.data

        except WebDriverException as e:
            logger.error(f"Browser error during scraping: {str(e)}")
            raise ValueError("Error accessing tender website. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            raise ValueError("An unexpected error occurred during scraping.")
        finally:
            if driver:
                driver.quit()

class ExcelReportGenerator:
    def __init__(self, data, filename="rasid_tenders_report.xlsx"):
        self.data = data
        self.filename = filename

    def generate_excel(self):
        try:
            df = pd.DataFrame(self.data)
            df.to_excel(self.filename, index=False)
            logger.info(f"Excel report generated: {self.filename}")
            return self.filename
        except Exception as e:
            logger.error(f"Error generating Excel report: {str(e)}")
            raise ValueError("Failed to generate report file.")

class EmailSender:
    def __init__(self, sender_email, password, receiver_emails):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = sender_email
        self.password = password
        self.receiver_emails = receiver_emails if isinstance(receiver_emails, list) else [receiver_emails]

    def send_email(self, attachment_filename):
        if not os.path.exists(attachment_filename):
            raise ValueError("Report file not found for email attachment.")

        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(self.receiver_emails)
        msg["Subject"] = f"Rasid Tenders Report - {datetime.date.today()}"

        body = """Hello,

Please find attached your personalized Rasid tender opportunities report.

This report contains tenders matching your selected category.

Regards,
Rasid Team
"""
        msg.attach(MIMEText(body, "plain"))

        try:
            with open(attachment_filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_filename)}"
                )
                msg.attach(part)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, self.receiver_emails, msg.as_string())
            
            logger.info("Email sent successfully!")
        except smtplib.SMTPException as e:
            logger.error(f"Email sending failed: {str(e)}")
            raise ValueError("Failed to send email. Please check your email settings.")
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            raise ValueError("An unexpected error occurred while sending email.")
        finally:
            try:
                os.remove(attachment_filename)
            except OSError:
                pass

class RasidJob:
    def __init__(self, sender_email, password, receiver_emails, category):
        self.sender_email = sender_email
        self.password = password
        self.receiver_emails = receiver_emails if isinstance(receiver_emails, list) else [receiver_emails]
        self.category = category

    def run(self):
        """Execute the full Rasid workflow with comprehensive error handling"""
        try:
            logger.info(f"Starting Rasid job for category: {self.category}")
            
            # Step 1: Scrape tender data
            scraper = TenderScraper(self.category)
            tender_data = scraper.scrape_tenders(max_pages=2)
            
            # Step 2: Generate Excel report
            report_generator = ExcelReportGenerator(tender_data)
            report_file = report_generator.generate_excel()
            
            # Step 3: Send email with report
            email_sender = EmailSender(
                sender_email=self.sender_email,
                password=self.password,
                receiver_emails=self.receiver_emails
            )
            email_sender.send_email(report_file)
            
            logger.info("Rasid job completed successfully")
            return True
            
        except ValueError as ve:
            logger.error(f"Validation error in Rasid job: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"Unexpected error in Rasid job: {str(e)}")
            raise ValueError("An unexpected error occurred while processing your request.")
