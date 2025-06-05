from django.shortcuts import render
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import csv
import io
import urllib.parse

# -------------------- View Functions --------------------

def homePage(request):
    return render(request, 'homePage.html')


def internship_view(request):
    internships_data = []
    csv_file = None

    if request.method == "POST":
        keyword = request.POST.get('keyword')
        num_internships = int(request.POST.get('num_internships'))
        save_csv = request.POST.get('save_csv') == 'true'

        internships_data = scrape_internshala_bs(keyword, num_internships)

        if save_csv:
            csv_file = f"{keyword}_internships.csv"
            save_to_csv(internships_data, csv_file)
            request.session['internships_data'] = internships_data

    return render(request, 'projects.html', {
        'internships': internships_data,
        'csv_file': csv_file
    })


def download_csv(request, filename):
    internships_data = request.session.get('internships_data', [])
    if not internships_data:
        return HttpResponse("No internship data found.", status=404)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    headers = ["Internship URL", "Title", "Company", "Location", "Start Date",
               "Duration", "Stipend", "Apply By", "Skills Required"]
    writer.writerow(headers)
    writer.writerows(internships_data)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

# -------------------- Core Scraping Logic --------------------

def scrape_internshala_bs(keyword, no_of_internship):
    keyword_encoded = urllib.parse.quote(keyword)
    base_url = f"https://internshala.com/internships/keywords-{keyword_encoded}/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    internships = soup.find_all('div', class_='individual_internship')[:no_of_internship]

    internships_list = []
    for internship in internships:
        link_tag = internship.find('a', href=True)
        if not link_tag:
            continue

        internship_url = urllib.parse.urljoin("https://internshala.com", link_tag['href'])
        detail_response = requests.get(internship_url, headers=headers)
        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

        # Extract using accurate classes
        title = detail_soup.find("div", class_="heading_4_5 profile").get_text(strip=True) if detail_soup.find("div", class_="heading_4_5 profile") else "N/A"
        company = detail_soup.find("a", class_="link_display_like_text").get_text(strip=True) if detail_soup.find("a", class_="link_display_like_text") else "N/A"

        location = detail_soup.find("div", {"id": "location_names"}).get_text(strip=True) if detail_soup.find("div", {"id": "location_names"}) else "N/A"
        
        start_span = detail_soup.find("span", {"class": "start_immediately_mobile"})
        start_date = start_span.get_text(strip=True) if start_span else "N/A"

        duration = "N/A"
        other_detail_blocks = detail_soup.find_all('div', class_='other_detail_item')
        for block in other_detail_blocks:
            heading = block.find('div', class_='item_heading')
            body = block.find('div', class_='item_body')
            if heading and body and 'Duration' in heading.get_text(strip=True):
                duration = body.get_text(strip=True)
                break
            
        stipend_span = detail_soup.find('span', class_='stipend')
        stipend = stipend_span.get_text(strip=True) if stipend_span else "N/A"

        apply_by_div = detail_soup.find('div', class_='other_detail_item apply_by')
        apply_by = apply_by_div.find('div', class_='item_body').get_text(strip=True) if apply_by_div else "N/A"


        # Skills
        skills_container = detail_soup.find('div', class_='round_tabs_container')
        if skills_container:
            skills = ", ".join([s.get_text(strip=True) for s in skills_container.find_all("span", class_='round_tabs')])
        else:
            skills = "N/A"


        internships_list.append([
            internship_url,
            title, company, location, start_date, duration, stipend, apply_by, skills
        ])

    return internships_list


def get_detail_value(soup, label):
    """
    Extract value from the Internship Detail page for a given label like Start Date, Duration, etc.
    """
    block = soup.find("div", class_="item_body", string=label)
    if block:
        parent = block.find_parent("div", class_="other_detail_item")
        if parent:
            value = parent.find("div", class_="item_body", recursive=False)
            return value.get_text(strip=True) if value else "N/A"
    return "N/A"


def save_to_csv(internships, filename="internships.csv"):
    headers = ["Internship URL", "Title", "Company", "Location", "Start Date",
               "Duration", "Stipend", "Apply By", "Skills Required"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(internships)


