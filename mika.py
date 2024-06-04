import openai
import pandas as pd
import yaml
from shutil import copyfile
from fastapi import FastAPI, HTTPException
from datetime import datetime
import subprocess
import requests
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib as mpl
from matplotlib.patches import Patch
import os, sys
from matplotlib.font_manager import FontProperties
font_path = '/Users/nurizaurulbaeva/Desktop/dejavu-fonts-ttf2/ttf/DejaVuSerif.ttf/'
from wordcloud import WordCloud, STOPWORDS
import jieba
import random
app = FastAPI(title='gpt-4', )

def load_api_key():
    try:
        with open("config.yaml") as f:
            config_yaml = yaml.safe_load(f)
        return config_yaml['api_key']
    except FileNotFoundError:
        print("config.yaml file not found. Make sure it exists in the correct location.")
        return None


openai.api_key = load_api_key()
file_path_xlsx = 'form_eng.xlsx'  # Changed variable name for clarity

def process_csv_and_generate_content(file_path_xls, name):
    try:
        df = pd.read_excel(file_path_xls)
        name_column = 'Student English name（ex：Eric Zhang or Runxin Zhang）Student Name (First Name + Last Name)'
        data = df[df[name_column] == name].astype(str)

        if data.empty:
            return None, "person not found", None, None, None, None, None, None

        words = data.iloc[:, 6:82].astype(str)
        basic_info = data.iloc[:, 6:10].astype(str)
        major_preferences = data.iloc[:, 14:37].astype(str)
        college_preferences = data.iloc[:, 37:49].astype(str)
        potential_major_exploration = data.iloc[:, 49:82].astype(str)
        column_AU = data.iloc[:, 46].astype(str)
        return words, data, name, basic_info, major_preferences, college_preferences, potential_major_exploration, column_AU
    except ValueError as e:
        print(f"Error reading the Excel file: {e}")
        return None, None, None, None, None, None, None, None


def word_cloud(words, file_path, font_path, name):
    # Creating a PNG file for the word cloud, focusing on the name in the middle of the picture
    stopwords = set(STOPWORDS)

    # Custom words to exclude from the word cloud
    custom_words = ["Strongly Agree", "Agree", "Moderately", "Strongly Disagree", "Skip", "Yes", "No", "Neutral", "Maybe", "Agree", "Strongly Agree", "Disagree", "Strongly Disagree"]

    # Update stopwords with custom words, except for the name
    stopwords.update(word.lower() for word in custom_words)
    stopwords.discard(name.lower())

    # Combine all words into a single string
    text = ' '.join(words.astype(str).values.flatten())

    # Emphasize the name in the word cloud
    text += (' ' + name) * 1000

    # Generate the word cloud
    wc = WordCloud(
        background_color='white',
        width=9000,
        height=6500,
        stopwords=stopwords,
        font_path=font_path,
        prefer_horizontal=1.0,
        collocations=False
    ).generate(text)

    # Display and save the word cloud image
    plt.figure(figsize=(9, 6.5), dpi=300)
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(file_path)
    plt.close()
    print(f"Word cloud image '{name}' created and saved to {file_path}")

    return file_path



# working over the spider chart creation. charts perform major direction of the student using information which chat gpt filtered from the whole database
def parse_generated_content(generated_visualization_score1, generated_visualization_score2):
    lines = generated_visualization_score1.strip().split('\n')+generated_visualization_score2.strip().split("\n")
    scores_dict = {}
    for line in lines:
        if "：" in line:
            category, scores_str = line.split("：", 1)
            category = category.split("（")[0]
            scores = []
            for score in scores_str.split(','):
                score_clean = score.strip("）").strip()
                if score_clean:
                    try:
                        scores.append(int(score_clean))
                    except ValueError:
                        print(f"Non-integer score encountered: '{score}'")
                        scores.append(0)
                else:
                    scores.append(0)
            if category in scores_dict and scores_dict[category]:
                scores_dict[category].extend(scores)
            else:
                scores_dict[category] = scores
    return scores_dict
    print(scores_dict)

    # Save the plot to a file
    file_name = os.path.join('/Users/nurizaurulbaeva/Desktop', filename)
    plt.savefig(file_name)
    plt.close()
    print(f"Saved: {file_name}")


def generate_gpt(data, name, basic_info, major_preferences, college_preferences, potential_major_exploration, column_AU):
    firstpage_summary = f"""  Your character is an elder writing to a student named ‘’’{name}’’’. Based on the questionnaire responses provided by the student (enclosed in three quotation marks), rewrite a narrative summary in the form of a letter. The letter should be in the second person, signed as ChatIvy, and should not exceed 750 words.. Please be consistent with the style in the following example: "Hello classmate, during this test, I saw a person. . . ;, Maintain the following structure and style: first paragraph, start by acknowledging the student's journey and expressing admiration for their openness and willingness to try new things. Mention their current grade and their chosen college major. In the second paragraph discuss the student's interests beyond the classroom, highlighting their engagement in literature and language as well as their balance between science and humanities. In the second paragraph mention the student's achievements, such as winning awards in competitions, and acknowledge their dedication and commitment.(if student do not have any achievements, you can skip this part). 
    In the third  paragraph,address any areas where the student seems unsure or hesitant, explaining that it is normal for interests to evolve over time.In the fourth paragraph, provide encouragement, emphasizing the importance of maintaining openness and curiosity, and reassure the student that success will follow if they stay true to themselves. In the fifth paragraph, conclude the letter with an encouraging note, signed as ChatIvy.
    You are a wise and knowledgeable researcher. You have inexhaustible curiosity, strong logic, and insights that are different from ordinary people. Your thirst for knowledge drives you to stand on the front line of exploring the unknown. Rational, you pay attention to logical analysis, are good at abstract thinking, and are always ready to find the truth, Please put appropriate spacing between paragraphs:'''{name},{basic_info}, {major_preferences}, {college_preferences}''' """
    major_prompt_one = f"""You are a top overseas education consultant with many years of experience in education, especially adept at understanding students' characteristics and making recommendations based on basic data. Your task is to help me recommend the most suitable majors for a high school student based on a questionnaire. You need to provide detailed reasons and incorporate details from the questionnaire in each reason, and you also need to provide sufficient reasoning process. In the questionnaire, the student will judge the weight of each question or factor, with different weights representing the importance of this factor in major selection (0 means not important at all, 5 means very important). Please give the final recommendations based on these weight numbers. Your specific task is divided into two steps. The first step is to recommend 10 most suitable majors for this student based on the information marked as 'Original Information' and provide reasons. The second step is to filter out 3 majors from the 10 most suitable majors recommended for this student based on the information marked as 'Supplementary Information' and provide reasons and the matching degree of these majors with the student.
    In the final result, I expect a document containing 10 recommended majors and reasons, 3 most suitable majors and reasons, with each reason being no less than 300 words. When you are ready, I will send you the student's information. Please put appropriate spacing between paragraphs"""
    major_prompt_two = f""" Please recommend 10 majors for the user based on the following questionnaire information. When making recommendations, please pay attention to the weights given by the student for each factor. Each recommendation reason should be no less than 300 words. Separate each recommended major with a blank line and form a numbered list: '''{name},{basic_info},{major_preferences}'''"""
    major_prompt_three = f"""  Please continue the second step by selecting the 3 most matching majors from the above 10 majors based on the following supplementary information (enclosed in triple quotes). Provide more detailed reasons for recommending these three majors, with sufficient details, evidence, and reasoning process. Each reason should be no less than 300 words. Also, provide the major match score (0 for least matching, 100 for most matching). Give reasons for each major in separate paragraphs, and include a blank line between each paragraph. The match score should be in parentheses after the major name. Make bold the major naming with corresponding score. '''{college_preferences}'''"""

    gpt_input = f"{firstpage_summary}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_summary = chat_completion.choices[0].message.content

    gpt_input = f"{major_prompt_one},{major_prompt_two},{name}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_major_prompt_two = chat_completion.choices[0].message.content

    gpt_input = f"{major_prompt_three}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_major_prompt_three = chat_completion.choices[0].message.content

    major_prompt_four = f"""Please list the English names of the three recommended majors from the previous response. Use this information: '''{generated_major_prompt_three}''', and add a blank line between the scores of the three majors."""
    gpt_input = f"{major_prompt_four}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    major_list = chat_completion.choices[0].message.content

    potential_major = f"""1. Study Difficulty: Some majors may involve a high level of study difficulty, such as requiring a deep understanding of complex theories and concepts, or needing to master a series of complex techniques and skills.
            2. Practical Opportunities: Some majors may lack sufficient practical opportunities, causing students to lack a connection between theory and practical application.
            3. Career Prospects: Some majors may lack clear or broad career prospects, making it difficult for students to find relevant jobs after graduation.
            4. Competitive Pressure: Some majors may have very high competitive pressure, such as popular majors where many students compete for limited job opportunities.
            5. Major Requirements: Some majors may have strict course or credit requirements, causing students to not have enough time and opportunities to explore their interests and potentials while meeting these requirements.
            6. Work Pressure: Some majors may lead to high-pressure jobs, such as fields like medicine, law, or finance, which often require working under high pressure and for long hours.
            7. Dependence on Economic Environment or Policies: Some majors may be affected by changes in the economic environment or policies, which could impact the job market and salary levels for that major. For example, finance or energy-related majors could be influenced by global economic or energy policy changes.
            8. Rapidly Changing Industry Environment: Some majors may face a rapidly changing industry environment, such as technology or media-related majors, where students need to continuously learn and update their knowledge and skills.

            You are now acting as a university advisor. Please provide the disadvantages of the following three majors based on the above 8 dimensions: '''{major_list}'''. Each dimension needs to be listed, and if there are no obvious disadvantages in a dimension, please state that directly.
            Try to be as detailed as possible and provide sufficient evidence and examples. Each point should be no less than 3 sentences. Try to add personal feelings to the descriptions to write the disadvantages in a more empathetic style. Add detailed examples after each reason, and make the reasons longer and more detailed. Separate the 8 dimensions of each major with a blank line, list the major name on a separate line as the title, and make each dimension a numbered list from 1 to 8 for each major.Please put appropriate spacing between paragraphs."""

    gpt_input = f"{potential_major}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_potential_major = chat_completion.choices[0].message.content

    Correspondence_college_recommendations = f"""The student hopes to study undergraduate in the following countries: USA, with possible majors being '''{major_list}'''. Please recommend two representative universities for each of the three majors in each of these countries and provide detailed reasons for the recommendations. Each reason should be no less than 300 words. Present the three majors in a numbered list format, and then provide the two recommended universities for each major in each of the student's preferred countries. Present the recommendations for each country's two universities for each major in a list format.Please put appropriate spacing between paragraphs."""

    Correspondence_Courses = f"""Assume the three most suitable majors you recommend for the user are '''{major_list}'''. Please list 7 foundational courses and 3 advanced courses for each major at the undergraduate level (in both Chinese and English). The format for the Chinese and English names should be: 专业名 (major name); 课程名 (class name)."""

    Major_development_history = f"""Please list the 5 most important turning points and their times and impacts in the past 50 years for each of the following three majors: '''{major_list}'''. Each description of the turning point and its impact should be no less than 200 words. Add a blank line between each turning point and the next. Add a blank line between each major and the next. Please put appropriate spacing between paragraphs"""

    Cutting_edge_field = f"""Please list 3 cutting-edge fields in academia and 3 cutting-edge fields in the industry for each of the following three majors: '''{major_list}'''. Provide detailed descriptions for each field, with each description no less than 200 words. Add a blank line between each field and the next. Add a blank line between each major and the next. Please put appropriate spacing between paragraphs """

    Visualization_p1 = f"""
    1. Knowledge Mastery: This dimension can be measured by testing or evaluating the student's understanding of core concepts and skills in the subject. This may include classroom performance, assignments, projects, test, and exam scores.
    2. Interest Level: This dimension can be measured through surveys or questionnaires to gauge the student's interest in the subject. This may include how often the student chooses to study the subject, the time they invest in it, and their self-motivation in the subject.
    3. Practical Application: This dimension can be assessed by evaluating the student's ability to apply their knowledge of the subject in practical scenarios. This may include their performance in experiments, projects, or internships, and how they apply what they have learned to real-world problems.
    4. Innovative Capability: This dimension can be measured by observing the student's innovative performance in the subject. This may include their ability to propose new ideas, new ways of solving problems, or creating new works.
    5. Future Commitment: This dimension can be measured by asking the student about their willingness to invest more time and effort in the subject in the future. This may include their plans for future work or further study in the field.
    Based on the following questionnaire results, please score the student's various subjects on these five dimensions (0-5 points), and return the results in the following format: 'Subject Name: Score, Score, Score, Score, Score'. Please add a blank line between the scores for each subject and ensure the use of Chinese subject names. Use this related information: '''{potential_major_exploration}''' Please directly provide scores without any analysis. The reference format is 5,5,5,5,5; 4,5,4,4,5; 5,4,5,5,4; 3,3,4,3,4. Please add a blank line between the scores for each subject."""

    Visualization_p2 = f"""Based on the following questionnaire results, please score the three most recommended majors for the student '''{major_list}''' on the corresponding five dimensions (0-5 points): '''{basic_info},{major_preferences},{college_preferences} '''. Please directly provide scores without any analysis. The reference format is 5,5,5,5,5; 4,5,4,4,5; 5,4,5,5,4; 3,3,4,3,4. Please add a blank line between the scores for each major."""

    Visualization_p3 = f"""Refer to the format and content in the paragraph enclosed in parentheses below and the student's questionnaire information, and write an in-depth analysis and a summary paragraph for the recommended majors '''{major_list}''' and their corresponding five dimensions: 'Knowledge Mastery', 'Interest Level', 'Practical Application', 'Innovative Capability', and 'Future Commitment'.
    (Example:
    Sports Medicine:
    - Knowledge Mastery: '''{name}''' has a strong interest and advantage in biological sciences during high school, which will help her grasp the relevant biological knowledge in sports medicine. In addition, her strongest subject within the natural sciences is biology, indicating that she may already have a certain foundation in biology. Therefore, '''{name}''' knowledge mastery in the field of sports medicine may be high, scoring 4.
    - Interest Level: '''{name}'''has clearly expressed her preference for working in fields related to sports medicine in her future career, indicating a high level of interest in this major. Moreover, her interest in extracurricular activities such as volleyball is also relevant to sports medicine. Thus, '''{name}''' interest level in the field of sports medicine may be high, scoring 5.
    - Practical Application: Sports medicine emphasizes practical application in treating and rehabilitating sports injuries. '''{name}''' has expressed a desire to work in areas related to sports rehabilitation in her future career, indicating a high demand and willingness for practical application. Additionally, she may have developed some practical skills in sports rehabilitation through activities such as volleyball, drama, and basketball. Therefore, '''{name}''' practical application ability in the field of sports medicine may be high, scoring 4.
    - Innovative Capability: The field of sports medicine requires continuous exploration of new treatment methods and rehabilitation techniques. '''{name}''' interest in literature during high school may help cultivate her innovative ability. Although innovation is not the most important characteristic in sports medicine, she may show some innovative potential in research and practice. Therefore, '''{name}''' innovative capability in the field of sports medicine may be relatively high, scoring 3.
    - Future Commitment: '''{name}'''has clearly expressed her interest in pursuing a career in fields related to sports medicine and rehabilitation in her future career preferences, indicating a high level of future commitment. Her family also provides financial support, which may offer her certain resources and opportunities in her studies and practice. Therefore, '''{name}''' future commitment in the field of sports medicine may be high, scoring 4.
    Considering '''{name}''' interests and evaluations in different subjects, the recommended majors include Sports Medicine, Rehabilitation Science, and Biological Sciences. '''{name}''' shows a high level of interest and matching in these fields. She has a good knowledge mastery and interest level in biology, demonstrates a high demand and willingness for practical application and future commitment. For innovative capability, '''{name}''' may need to further cultivate and improve it in these subjects. It is suggested that '''{name}'''comprehensively consider her/his interests and overall abilities when choosing a major, and have a clear understanding of her future career plans to make the best decision for herself.)"""

    Highschool_activities = f"""Your current role is that of a seasoned college advisor. Based on the style, content, and format of the paragraph in parentheses below, plan university application activities for this high school student. Their target majors are: '''{major_list}'''. The activity planning framework includes: activities within one week (visits, lectures), activities within one month (summer school, reading, small research projects, Coursera courses), activities within one year (research, internships, volunteering), and background enhancement plans (mainly research and open-ended project-based learning, using both free and paid resources).
    Please provide creative and unique activity plans. Each activity's details and information should be no less than 300 words. Separate the content of activities within one week, within one month, within one year, and background enhancement plans with blank lines, and use titles for each section: Activities within One Week, Activities within One Month, Activities within One Year, and Background Enhancement Plans. Add a blank line between each major.
    (1. Kinesiology:
    Within One Week: Within one week, you can organize a small kinesiology seminar at your school. Invite sports enthusiasts, fitness coaches, and students from related fields to participate. You can invite a professor or expert in kinesiology to give a lecture on hot topics such as the relationship between exercise and health, emerging exercise training methods, etc. Through this unique event, you will demonstrate your organizational and leadership skills and provide valuable learning opportunities for your peers.
    Within One Month: Within one month, you can participate in a science popularization activity on an online social platform. You can create short videos or write blog posts introducing interesting scientific experiments or exercise principles. Such activities will help you spread kinesiology knowledge to a broader audience while honing your science communication skills. You can also collaborate with graduate students or professors to create an interesting and in-depth science series.
    Within One Year: Within one year, you can organize a large-scale kinesiology experiment event. You can cooperate to establish a temporary fitness testing center and invite students and community members to participate. You can design various test items, such as cardiovascular function tests, muscle strength tests, etc., and provide personalized health advice to participants. Through this activity, you will develop project management, teamwork, and data analysis skills while serving the community and promoting health concepts.
    Background Enhancement Plan: In addition to participating in academic and practical activities, you can consider planning an innovative "Kinesiology Exhibition." You can use virtual reality technology to create an immersive exhibition environment where visitors can personally experience different types of exercise and their effects on the body. You can collaborate with designers, programmers, and medical experts to create an engaging and educational exhibition to showcase the charm of kinesiology.
    2. Biology:
    Within One Week: Within one week, you can initiate an on-campus ecological exploration activity. Invite classmates to visit nearby nature reserves or wild areas to conduct a biodiversity survey. You can lead the group in observing different species of plants and animals, recording their distribution and behavior. Through this activity, you will cultivate classmates' field observation skills and enhance their understanding of ecosystems.
    Within One Month: Within one month, you can launch a "Biological Stories Collection Plan." Invite people around you, including the elderly, farmers, fishermen, etc., to share their interaction experiences and traditional knowledge with nature. You can interview them, record these interesting biological observations and legends, and compile them into books, blogs, or short films. Through this plan, you will inherit local biological culture and promote the value of biological sciences.
    Within One Year: Within one year, you can initiate an "Urban Ecological Restoration Plan." Collaborate with classmates to select a damaged ecological environment on campus or in the community, such as wasteland or polluted areas, and design and implement an ecological restoration plan. You can plant adaptive plants, introduce natural enemies, and monitor environmental changes. Through this project, you will develop project management and environmental protection skills while contributing to urban ecological improvement.
    Background Enhancement Plan: In addition to academic and practical activities, you can consider participating in a "Biological Culture Exchange Plan." You can apply to visit other countries or regions to work with local biologists, folk artists, and community leaders to learn about their biological cultural traditions. You can learn local field observation methods, herbal medicine, traditional stories, etc., to expand your biological sciences horizons. Combining these experiences with your professional knowledge to create unique research or projects.
    3. Physical Therapy:
    Within One Week: Within one week, you can organize a "Rehabilitation Exercise Experience Day." Invite community members, especially those with sports injuries or chronic diseases, to participate in a relaxed and enjoyable outdoor activity. You can design a series of simple rehabilitation exercises such as stretching, balance training, and mild aerobic exercises. Through this activity, you will help participants experience the positive effects of physical therapy while enhancing their health awareness.
    Within One Month: Within one month, you can initiate a "Rehabilitation Science Popularization Picture Book Creation Project." Collaborate with art students to create an interesting picture book that introduces the basic principles and methods of rehabilitation therapy. You can select some common rehabilitation cases and present scientific knowledge with creative stories and illustrations. This picture book can be used in children's hospitals, rehabilitation centers, etc., to help patients and families understand rehabilitation therapy.
    Within One Year: Within one year, you can collaborate to develop a "Virtual Rehabilitation Laboratory." Using virtual reality technology, create a virtual environment that simulates various rehabilitation training scenarios. Users can experience different types of exercise, balance, and rehabilitation training through VR headsets while receiving professional guidance in the virtual environment. This project combines technology and rehabilitation practice to provide innovative rehabilitation experiences for patients.
    Background Enhancement Plan: In addition to participating in regular internships and research activities, you can consider establishing a "Community Rehabilitation Support Group." You can regularly organize rehabilitation knowledge sharing sessions to provide rehabilitation advice and guidance for community members. You can also collaborate with community sports clubs to offer customized rehabilitation training programs. Through this support group, you will deepen your understanding of patient needs while enhancing your rehabilitation consulting and communication skills.)
    Please put appropriate spacing between paragraphs.
    """

    gpt_input = f"{Correspondence_college_recommendations}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_Correspondence_college_recommendations = chat_completion.choices[0].message.content

    gpt_input = f"{Correspondence_Courses}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_Correspondence_Courses = chat_completion.choices[0].message.content

    gpt_input = f"{Major_development_history}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_Major_development_history = chat_completion.choices[0].message.content

    gpt_input = f"{Cutting_edge_field}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_Cutting_edge_field = chat_completion.choices[0].message.content

    gpt_input = f"{Visualization_p1}"
    chat_completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_visualization_score1 = chat_completion.choices[0].message.content

    gpt_input = f" {Visualization_p2}"
    chat_completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_visualization_score2 = chat_completion.choices[0].message.content

    gpt_input = f"{Visualization_p3}"
    chat_completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_visualization_p3 = chat_completion.choices[0].message.content

    gpt_input = f"{Highschool_activities}"
    chat_completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_input}],
        temperature=0.2,
        top_p=0.5,
        frequency_penalty=0.7,
        presence_penalty=0.0
    )
    generated_Highschool_activities = chat_completion.choices[0].message.content

    generated_content = [
        generated_summary,
        generated_major_prompt_two,
        generated_major_prompt_three,
        major_list,
        generated_potential_major,
        generated_Correspondence_college_recommendations,
        generated_Correspondence_Courses,
        generated_Major_development_history,
        generated_Cutting_edge_field,
        generated_visualization_score1,
        generated_visualization_score2,
        generated_visualization_p3,
        generated_Highschool_activities,
    ]
    return generated_content



def check_pdflatex():
    try:
        result = subprocess.run(['pdflatex', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False


def populate_template(template_path, output_path, content_dict):
    with open(template_path, 'r') as file:
        template_content = file.read()

    for placeholder, value in content_dict.items():
        template_content = template_content.replace(placeholder, value)

    with open(output_path, 'w') as file:
        file.write(template_content)


def generate_pdf(latex_file_path, output_dir):
    try:
        result = subprocess.run(['pdflatex', latex_file_path], cwd=output_dir, check=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        print("PDF generated successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to generate PDF:", e)


@app.get("/generate_pdf")
def main():
    print("Starting process...")
    file_path_xlsx = 'form_eng.xlsx'
    name = 'Albert Yin'

    words, data, name, basic_info, major_preferences, college_preferences, potential_major_exploration, column_AU = process_csv_and_generate_content(
        file_path_xlsx, name)

    if data is None:
        print("No data found for the provided name.")
        return {"message": "No data found for the provided name."}

    generated_content = generate_gpt(data, name, basic_info, major_preferences, college_preferences,
                                     potential_major_exploration, column_AU)
    print("GPT content generation completed")

    # Generate word cloud
    font_path = '/Users/nurizaurulbaeva/Desktop/dejavu-fonts-ttf2/ttf/DejaVuSerif.ttf'
    word_cloud_file_path = f'/Users/nurizaurulbaeva/Desktop/{name}_word_cloud.png'
    word_cloud(words, word_cloud_file_path, font_path, name)

    # Parse generated content for visualization
    generated_visualization_score1, generated_visualization_score2 = generated_content[-3], generated_content[-2]
    scores_dict = parse_generated_content(generated_visualization_score1, generated_visualization_score2)

    # Use the template to create the final content
    template_path = 'pro[1].tex'
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    tex_path = f'/Users/nurizaurulbaeva/Desktop/ChatIvy_{name}_{current_time}.tex'
    pdf_output_path = f'/Users/nurizaurulbaeva/Desktop/ChatIvy_{name}.pdf'

    content_dict = {
        "%name%": name,
        "image": word_cloud_file_path,
        "%generated_summary%": generated_content[0],
        "%generated_major_prompt_two%": generated_content[1],
        "%generated_major_prompt_three%": generated_content[2],
        "%major_list%": generated_content[3],
        "%generated_potential_major%": generated_content[4],
        "%generated_Correspondence_college_recommendations%": generated_content[5],
        "%generated_Correspondence_Courses%": generated_content[6],
        "%generated_Major_development_history%": generated_content[7],
        "%generated_Cutting_edge_field%": generated_content[8],
        "%generated_visualization_p3%": generated_content[11],
        "%generated_Highschool_activities%": generated_content[12]
    }
    populate_template(template_path, tex_path, content_dict)

    if check_pdflatex():
        generate_pdf(tex_path, "/Users/nurizaurulbaeva/Desktop")
        print(f"PDF generated at {pdf_output_path}")
        return {"message": "PDF generated successfully.", "pdf_path": pdf_output_path}
    else:
        print("pdflatex is not installed.")
        return {"message": "pdflatex is not installed."}


if __name__ == "__main__":
    main()
