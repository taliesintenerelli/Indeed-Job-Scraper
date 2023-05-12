import urllib
import undetected_chromedriver as uc
from time import sleep
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pandas as pd


def make_url(location, search, page):
    getVars = {'q': search, 'l': location, 'formage': 'last', 'sort': 'date', 'start': page}
    page_url = 'https://www.indeed.com/jobs?' + urllib.parse.urlencode(getVars)
    return page_url

# takes url and uses selenium to get the html
def get_html(url, driver):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup

# takes a job card html and retrieves the job title
def get_job_title(job_card):
    job_title = job_card.find('h2', {'tabindex': '-1'})
    if job_title != None:
        return job_title.find('a').text
    else:
        return ''

# takes a job card html and retrieves the company name
def get_company_name(job_card):
    company_name = job_card.find('span', {'class': 'companyName'})
    if company_name != None:
        return company_name.text
    else:
        return ''

# takes a job card html and retrieves the post date
def get_job_location(job_card):
    location = job_card.find('div', {'class': 'companyLocation'})
    if location != None:
        return location.text
    else:
        return ''

# Find all the elements with the same tag name and itirate over the number of elements per page to append each elements url to new_urls_list
def get_urls_list(driver, url):
    # This part checks if there is a promo card and looks for one more url if there is because there is a h2 tag in the promo card html code
    new_urls_list = []
    promo = driver.find_elements(By.CLASS_NAME, "promoCard mobile")
    if promo != None:
        max = 15
    else:
        max = 14

    # This part gets the urls and puts them in new_url_list
    count = 0
    while count <= max:
        try: elements = driver.find_elements(By.TAG_NAME, "h2")
        except: break
        element = elements[count]
        try: element.click()
        except: break
        sleep(2)
        new = driver.current_url
        new_urls_list.append(new)
        count += 1
    return new_urls_list

# Takes in a list of urls and returns the description list and boj type list
def get_description_and_type_list(driver, new_urls_list):
    # create empty lists to hold the descriptions and job types
    description_list = []
    job_type_list = []

    # iterate through the urls
    for new_url in new_urls_list:
        driver.get(new_url)
        sleep(3)
        # Get description text from each url and append ut to description_list
        description = driver.find_element(By.ID, "jobDescriptionText")
        text = description.text.strip()
        clean_text = ' '.join(text.split())
        description_list.append(clean_text)
        # Get job title from each url to use in following code chuck to determine the value to store in job_type
        index = new_urls_list.index(new_url)
        titles = driver.find_elements(By.TAG_NAME, "h2")
        title = titles[index]
        title = str(title.text)
        # determine job_type from the job type section of the url, the job title, and the description text, and then append it to job_type_list
        try:
            job_type = driver.find_element(By.ID, "salaryInfoAndJobType")
            job_type = job_type.text
            if 'Full' in job_type: job_type = 'Full-Time'
            elif 'Part' in job_type: job_type = 'Part-Time'
            elif 'Contract' in job_type: job_type = 'Contract'
            else: job_type = 'Full-Time'
            if 'Intern' in job_type or 'intern ' in clean_text.lower() or 'internship' in clean_text.lower() or 'intern' in title.lower() or 'internship' in title.lower(): job_type = 'Internship'
            job_type_list.append(job_type)
        except:
            job_type_list.append('Full-Time')

    return description_list, job_type_list




# takes the page url and uses previouse functions to return a list of links, a list of descriptions, and a list of job types for each job in the argument url
def get_descriptions_links_jobTypes(url, driver):

    # navigate to the page
    driver.get(url)

    # get list of job urls and store it in new_urls_list
    new_urls_list = get_urls_list(driver, url)

    # Itterate over the urls and add the description to the description_list and the job tyles to the job type list
    description_list, type_list = get_description_and_type_list(driver, new_urls_list)

    # put the list of urls and a list of descriptions into a list of lists and return the final list
    list_of_lists = [new_urls_list, description_list, type_list]

    # Delet duplicates in the lists. I do this because whenever there is a promo card it makes two coppies of the previouse job card information
    inner_list = list_of_lists[0]
    for i in range(len(inner_list) - 1):
        if inner_list[i] == inner_list[i + 1]:
            for j in list_of_lists:
                j.remove(j[i])
            break

    return list_of_lists[0], list_of_lists[1], list_of_lists[2]

# takes in a url nad driver and uses previouse functions to return a job title list, company name list, and location list for the job listings under that url
def get_title_name_location(url, driver):
    # Create empty lists
    title_list = []
    company_name_list = []
    location_list = []
    # Get the site html to extract info from
    html = get_html(url, driver)
    job_list_html = html.find_all('div', attrs={'class': 'job_seen_beacon'})  # 'jobsearch-ResultsList css-0'})
    # Iterate through the cards holding the job info. If there is info in them append them to the appropriate list
    for i in job_list_html:
        title = get_job_title(i)
        if title == '':
            continue
        title_list.append(title)

        name = get_company_name(i)
        if name == '':
            continue
        company_name_list.append(name)

        location = get_job_location(i)
        if location == '':
            continue
        location_list.append(location)

    return title_list, company_name_list, location_list

# this function uses all previouse functions to return a 2D list of raw data
def get_raw_data_list(select_location, search):
    # Create selenium chrome driver
    driver = uc.Chrome()
    # Make empty lists
    title_list = []
    name_list = []
    location_list = []
    link_list = []
    description_list = []
    type_list = []

    check = ''
    # Iterate through a certain number of pages and use previous functions to compile a list of raw data
    for i in range(2):
        # Create main page url
        page = '0' + str(i)
        url = make_url(select_location, search, page)
        print(url)
        # Use previous functions to get data
        title, name, location = get_title_name_location(url, driver)
        link, description, type = get_descriptions_links_jobTypes(url, driver)
        # Change job_type to "Internship" if the corresponding job title (pushed to lower case) includes the string 'intern ', 'internship', or 'Internship'
        for i in range(len(title)):
            if 'intern ' in title[i].lower() or 'internship' in title[i].lower(): type[i] = 'Internship'
        # Check if "turning" to the next page gave a different set of results and break the for loop if not
        if check == description: break
        check = description
        # Append the lists for each page to the larger lists containing the data from all the pages
        title_list += title
        name_list += name
        location_list += location
        link_list += link
        description_list += description
        type_list += type

    raw_data_list = [title_list, name_list, location_list, link_list, description_list, type_list]

    driver.quit()

    return raw_data_list

# This function interacts with the user to get the proper perameters to feed the get_raw_data_list function, it then calls the get_raw_data_list and returns the resulting list
def get_user_input():
    # Get location, job type, and job field
    input_location = input("Please input a location for me to search for jobs that are inside of. The more general the location the better, such as a country instead of a state, or a state instead of a city.\n> ")
    input_type = input("Please select your desired job type (type the associated letter into the input field):\n  a) Internship\n  b) Full-Time \n  c) Part-Time\n  d) Contract\n  e) All\n> ")
    input_field = input("Please select your desired job field (type the associated letter into the input field):\n  a) Data Analyst\n  b) Data Scientist \n  c) Data Engineering\n  d) Machine Learning\n  e) & f) Other: If you select this option you will be able to customize the work field title you want to search for, but the \n     results will not be ranked by relevance to your skills because I have not yet developed a set of skills to look for that\n     are relevant to other fields. If you would like to provide your own job field search along with a skill list for the\n     program to rank your job listings by, enter \"f\". Otherwise enter \"e\" to get unranked job listings for a job field of your choice.\n> ")
    if input_type.lower() == 'a':
        input_type = 'intern'
    if input_type.lower() == 'b':
        input_type = ''
    if input_type.lower() == 'c':
        input_type = 'part time'
    if input_type.lower() == 'd':
        input_type = 'contract'
    if input_type.lower() == 'e':
        input_type = ''
    # Create list of possible skills for the program to sort for and turn it into a comma separated string
    skills_library = ['Python', 'SQL', 'AWS', 'Spark', 'Azure', 'R', 'Tableau', 'Java', 'Excel', 'Scala', 'Hadoop',
                      'Power BI', 'Snowflake', 'Kafka', 'NoSQL', 'DataBricks', 'Redshift', 'Get', 'Oracle',
                      'Airflow', 'GCP', 'Docker', 'SQL Server', 'SAS', 'Kubernetes', 'Go', 'PySpark', 'Pandas',
                      'MySQL', 'MongoDB', 'Shell', 'TensorFlow', 'Flow', 'Linux', 'Word', 'BigQuery', 'Cassandra',
                      'PowerPoint', 'JavaScript', 'C++', 'Jira', 'PyTorch', 'SAP', 'Jenkins', 'NumPy', 'PostgreSQL',
                      'Scikit-learn', 'GitHub', 'Terraform', 'SSIS', 'C#', 'Qlik', 'Looker', 'Alteryx', 'C', 'Unix',
                      'Keras', 'MATLAB', 'Elasticse...', 'VBA', 'Windows', 'Bash', 'SPSS', 'DynamicDB',
                      'Confluence', 'Jupyter', 'GitLab', 'React', 'T-SQL']
    skills_library_string = ''
    for i in range(len(skills_library)):
        skills_library_string += skills_library[i]
        if i != len(skills_library) - 1:
            skills_library_string += ', '
    # Get skills that the user wants to search for.
    if input_field.lower() == 'a':
        input_field = 'data analyst'
        print('Enter a list of skills that you have separated by commas so that I can look to see which of your skills are most desired by\npotential employers, and so that I can rank the job listings I find by how many of your skills that they mention. The Following is\na list of the most commonly asked for skills, so include anything from this list that you know as well as anything else that you\n think would be valuable to employers. Make sure to spell everything correctly with correct capatalizations.')
        print(skills_library_string)
        skills = input('> ')
    if input_field.lower() == 'b':
        input_field = 'data science'
        print('Enter a list of skills that you have separated by commas so that I can look to see which of your skills are most desired by\npotential employers, and so that I can rank the job listings I find by how many of your skills that they mention. The Following is\na list of the most commonly asked for skills, so include anything from this list that you know as well as anything else that you\n think would be valuable to employers. Make sure to spell everything correctly with correct capatalizations.')
        print(skills_library_string)
        skills = input('> ')
    if input_field.lower() == 'c':
        input_field = 'data engineer'
        print('Enter a list of skills that you have separated by commas so that I can look to see which of your skills are most desired by\npotential employers, and so that I can rank the job listings I find by how many of your skills that they mention. The Following is\na list of the most commonly asked for skills, so include anything from this list that you know as well as anything else that you\n think would be valuable to employers. Make sure to spell everything correctly with correct capatalizations.')
        print(skills_library_string)
        skills = input('> ')
    if input_field.lower() == 'd':
        input_field = 'machine learning'
        print('Enter a list of skills that you have separated by commas so that I can look to see which of your skills are most desired by\npotential employers, and so that I can rank the job listings I find by how many of your skills that they mention. The Following is\na list of the most commonly asked for skills, so include anything from this list that you know as well as anything else that you\n think would be valuable to employers. Make sure to spell everything correctly with correct capatalizations.')
        print(skills_library_string)
        skills = input('> ')
    if input_field.lower() == 'e':
        input_field = input('Enter your desired job field. Make sure it is spelled correctly and no more than 3 words\nbecause the program will reject listings that dont include what you enter here.\n> ')
        skills = 'N/A'
    if input_field.lower() == 'f':
        input_field = input('Enter your desired job field. Make sure it is spelled correctly and no more than 3 words\nbecause the program will reject listings that dont include what you enter here.\n> ')
        skills = input("Enter your skills separated by commas. Make sure everything is spelled correctly.\n> ")
    # Use previously collected information to create a search term for the url
    search = input_field + ' ' + input_type
    # "R" is a commmon skill but is also just aletter and can be accidentally found by the program when it is not there so this chunk of code is so that when the code
    # is looking for R it doesn't mistake it for just the capital letter R used regularly in a sentence
    skills_list = skills.split(',')
    skills_list = [s.strip() for s in skills_list]
    if 'R' in skills_list:
        index = skills_list.index('R')
        skills_list.pop(index)
        skills_list.append(' R ')
        skills_list.append('R,')
        skills_list.append('R.')

    return search, input_location, skills_list, input_type, input_field

def get_clean_data():
    # Get user input and raw data which takes the form raw_data_list = [title_list, name_list, location_list, link_list, description_list, type_list]
    search, input_location, skills_list, input_type, input_field = get_user_input()
    raw_data_list = get_raw_data_list(input_location, search)

    # Change names ocf some of the input field types to make them easier to search for
    if input_field == 'data science': input_field = 'data scien'
    if input_field == 'data analyst': input_field = 'data analys'

    # Itirate through the descriptions to get the index for each job. For each job index, check the various attributes to see if it is of the desired job type
    # and place "None" in the 4 element of each job index if it is not of the right type
    for description in raw_data_list[4]:
        index = raw_data_list[4].index(description)
        type = raw_data_list[5][index]

        if input_type != '':
            if input_type.lower() not in raw_data_list[4][index].lower() and type.lower() not in raw_data_list[0][index].lower() and type.lower() not in raw_data_list[5][index].lower():
                raw_data_list[2][index] = "None"
        if input_type == '':
            if 'intern ' in raw_data_list[4][index].lower() or 'internship' in raw_data_list[4][index].lower() or 'part-time' in raw_data_list[4][index].lower() or 'contract' in raw_data_list[0][index].lower() or 'intern ' in raw_data_list[0][index].lower() or 'part-time' in raw_data_list[0][index].lower():
                raw_data_list[2][index] = "None"

        if input_field.lower() not in raw_data_list[0][index].lower():# and input_field.lower() not in raw_data_list[4][index].lower():
            raw_data_list[2][index] = "None"
    # Delete all the jobs for which the previous code placed "None" in the 2nd attribute of
    while "None" in raw_data_list[2]:
        index = raw_data_list[2].index("None")
        for i in raw_data_list:
            i.pop(index)

    # Append 2 more lists to the main list
    raw_data_list.append([])
    raw_data_list.append([])

    # Put the overlaping skills into the corresponding element of the first of the new lists that were just added to the main list
    for description in raw_data_list[4]:
        raw_data_list[6].append('')
        raw_data_list[7].append('')
        index = raw_data_list[4].index(description)
        for skill in skills_list:
            if skill in description:
                raw_data_list[6][index] += skill + ', '
        # Delete duplicates of R from when I created multiple for ease of search
        if ' R ,' in raw_data_list[6][index]: raw_data_list[6][index] = raw_data_list[6][index].replace(' R ,', 'R,')
        if 'R,,' in raw_data_list[6][index]: raw_data_list[6][index] = raw_data_list[6][index].replace(' R,,', ' R,')
        if 'R.,' in raw_data_list[6][index]: raw_data_list[6][index] = raw_data_list[6][index].replace(' R.', ' R,')
        num_r = raw_data_list[6][index].count('R,')
        raw_data_list[6][index] = raw_data_list[6][index].replace('R,', '', num_r - 1)

    # Count the number of oberlaping skills for each job and put the number in the corresponding element of the second one of the two new lists that were just added to the main list
    for index in range(len(raw_data_list[6])):
        overlap = raw_data_list[6][index]
        overlap_list = overlap.split(',')
        raw_data_list[7][index] = len(overlap_list) - 1

    # Put the jobs in order of most to least number of overlaping skills and place this new arrangement into clean_data_list
    clean_data_list = [[],[],[],[],[],[],[],[]]
    count = 20
    while count >= 0:
        try:
            while True:
                index = raw_data_list[7].index(count)
                for i in range(len(raw_data_list)):
                    clean_data_list[i].append(raw_data_list[i][index])
                    raw_data_list[i].pop(index)
        except ValueError:
            count -= 1
            continue
        count -= 1

    return clean_data_list

def add_to_csv(two_d_list):
    # Create a data frame object
    df = pd.DataFrame(two_d_list)

    # Write the data frame to a CSV file
    df.to_csv('data.csv', index=False, header=False)

# Execute program
list = get_clean_data()
add_to_csv(list)