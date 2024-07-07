import openai

def summarize_hospitals(openai_api_key, hospital_details):
    openai.api_key = openai_api_key

    summary_message = [
        f"{i+1}. {hospital.get('name', 'Unknown')}: {hospital.get('formatted_address', 'Address not available')}\n"
        f"Rating: {hospital.get('rating', 'Rating not available')}\n"
        f"Phone: {hospital.get('formatted_phone_number', 'Phone number not available')}\n"
        for i, hospital in enumerate(hospital_details[:5])
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a hospital analyzer, skilled in prioritizing best hospitals based on value."},
            {"role": "user", "content": f"Summarize and prioritize the value of below hospitals:\n{''.join(summary_message)}"}
        ]
    )

    return response.choices[0].message['content']
