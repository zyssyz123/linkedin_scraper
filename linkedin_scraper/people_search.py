import os
from typing import List
from time import sleep
import urllib.parse

from .objects import Scraper
from .jobs import Job

class PeopleSearch(Scraper):
    AREAS = ["recommended_jobs", None, "still_hiring", "more_jobs"]

    def __init__(self, driver, base_url="https://www.linkedin.com/", close_on_complete=False, scrape=True, scrape_recommended_jobs=True):
        super().__init__()
        self.driver = driver
        self.base_url = base_url

        if scrape:
            self.scrape(close_on_complete, scrape_recommended_jobs)


    def scrape(self, close_on_complete=True, scrape_recommended_jobs=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete, scrape_recommended_jobs=scrape_recommended_jobs)
        else:
            raise NotImplemented("This part is not implemented yet")


    def scrape_people_card(self, base_element) -> Job:
        title_span = self.wait_for_element_to_load(name="entity-result__title-text", base=base_element)
        people_link = self.wait_for_element_to_load(name="app-aware-link", base=title_span)
        return people_link.get_attribute("href").split("?")[0]


    def scrape_logged_in(self, close_on_complete=True, scrape_recommended_jobs=True):
        driver = self.driver
        driver.get(self.base_url)
        if scrape_recommended_jobs:
            self.focus()
            sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)
            job_area = self.wait_for_element_to_load(name="scaffold-finite-scroll__content")
            areas = self.wait_for_all_elements_to_load(name="artdeco-card", base=job_area)
            for i, area in enumerate(areas):
                area_name = self.AREAS[i]
                if not area_name:
                    continue
                area_results = []
                for job_posting in area.find_elements_by_class_name("jobs-job-board-list__item"):
                    job = self.scrape_people_card(job_posting)
                    area_results.append(job)
                setattr(self, area_name, area_results)
        return


    def search(self, search_term: str) -> List[dict]:
        url = os.path.join(self.base_url, "search/results/people/") + f"?keywords={urllib.parse.quote(search_term)}&refresh=true"
        self.driver.get(url)
        
        sleep(5)  
        
        self.scroll_to_bottom()
        sleep(2)  
        
        people_list_class_name = "IxlEPbRZwQYrRltKPvHAyjBmCdIWTAoYo"
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, people_list_class_name))
            )
        except Exception as e:
            print(f"Waiting for element error: {str(e)}")
        
        try:
            for percent in [0.3, 0.6, 1.0]:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight * arguments[0]);", 
                    percent
                )
                sleep(2)  
        except Exception as e:
            print(f"Scrolling error: {str(e)}")
        
        people_profiles = []
        try:
            people_cards = self.driver.find_elements("class name", "IxlEPbRZwQYrRltKPvHAyjBmCdIWTAoYo")
            print(f"Found {len(people_cards)} profile cards")
        except Exception as e:
            print(f"Error finding profile cards: {str(e)}")
            people_cards = []
        
        # Now iterate through the profile cards
        for card in people_cards:
            try:
                profile_links = card.find_elements("class name", "eETATgYTipaVsmrBChiBJJvFsdPhNpulhPZUVLHLo")
                
                if profile_links and len(profile_links) > 1:
                    profile_link = profile_links[1].get_attribute("href")
                elif profile_links:
                    profile_link = profile_links[0].get_attribute("href")
                else:
                    continue  
                
                # Extract profile information
                profile_data = {}
                
                # Store the profile URL
                if profile_link and "/in/" in profile_link:
                    # Extract the profile URL and miniProfile URN
                    profile_data["profile_url"] = profile_link.split("?")[0]
                    
                    # Extract the mini profile URN if available
                    if "miniProfileUrn=" in profile_link:
                        mini_profile_urn = profile_link.split("miniProfileUrn=")[1].split("&")[0]
                        profile_data["mini_profile_urn"] = urllib.parse.unquote(mini_profile_urn)
                    
                    # Try to get the profile name
                    try:
                        if profile_links and len(profile_links) > 1:
                            name_element = profile_links[1]
                            spans = name_element.find_elements("tag name", "span")
                            if spans and len(spans) > 0:
                                for span in spans:
                                    name_text = span.text.strip()
                                    if name_text and "查看" not in name_text and "的档案" not in name_text:
                                        profile_data["name"] = name_text
                                        break
                            else:
                                profile_data["name"] = name_element.text.strip()
                        else:
                            profile_data["name"] = "Unknown"
                    except Exception as name_err:
                        print(f"Error extracting name: {str(name_err)}")
                        profile_data["name"] = "Unknown"
                        
                    try:
                        job_elements = card.find_elements("class name", "LjmdKCEqKITHihFOiQsBAQylkdnsWhqZii")
                        if job_elements and len(job_elements) > 0:
                            profile_data["title"] = job_elements[0].text.strip()
                    except:
                        pass

                    try:
                        location_elements = card.find_elements("class name", "cTPhJiHyNLmxdQYFlsEOutjznmqrVHUByZwZ")
                        if location_elements and len(location_elements) > 0:
                            profile_data["location"] = location_elements[0].text.strip()
                    except:
                        pass
                        
                    people_profiles.append(profile_data)
            except Exception as e:
                print(f"Error extracting profile data: {str(e)}")
                continue
                
        return people_profiles