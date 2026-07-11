import os
import random
import pickle
from transformers import AutoTokenizer

first_names = ["Aditya", "Aarav", "Arjun", "Vivaan", "Vihaan", "Krishna", "Rohan", "Rahul", "Karan", "Ankit", "Aman", "Siddharth", "Harsh", "Ayush", "Yash", "Nikhil", "Manav", "Dhruv", "Aryan", "Kabir", "Ishaan", "Om", "Pranav", "Ritvik", "Shivam", "Akash", "Abhishek", "Rajat", "Varun", "Tanish", "Mihir", "Soham", "Dev", "Rishi", "Tejas", "Chirag", "Neel", "Parth", "Arnav", "Laksh", "Hardik", "Vipul", "Ameya", "Neet", "Jatin", "Aditi", "Ananya", "Priya", "Sneha", "Neha", "Pooja", "Kavya", "Riya", "Diya", "Meera", "Ishita", "Nandini", "Anushka", "Shruti", "Sakshi", "Khushi", "Simran", "Swati", "Avni", "Tanvi", "Radhika", "Shreya", "Palak", "Muskan", "Vidhi", "Trisha", "Manya", "Aarohi", "Saanvi", "Myra", "Kiara", "Navya", "Prisha", "Vaishnavi", "Aisha", "Charvi", "Anvi", "Bhavya", "Jhanvi", "Vaidahi", "Gaurika", "Janhavi", "Aarya", "Ankita", "Swara", "James", "Emily", "Michael", "Sophia", "William", "Olivia", "Alexander", "Emma", "Daniel", "Charlotte", "Benjamin", "Amelia", "Lucas", "Isabella", "Ethan", "Mia", "Noah", "Grace", "Henry", "Chloe"]
last_names = ["Sharma", "Verma", "Singh", "Patel", "Gupta", "Agarwal", "Jain", "Mehta", "Shah", "Joshi", "Kulkarni", "Deshmukh", "Patil", "Pawar", "Chauhan", "Yadav", "Mishra", "Pandey", "Tiwari", "Dubey", "Tripathi", "Saxena", "Sinha", "Roy", "Ghosh", "Banerjee", "Mukherjee", "Chatterjee", "Bose", "Das", "Nair", "Menon", "Pillai", "Iyer", "Iyengar", "Reddy", "Rao", "Naidu", "Shetty", "Hegde", "Bhat", "Acharya", "Gowda", "Kumar", "Choudhary", "Malhotra", "Kapoor", "Khanna", "Arora", "Sethi", "Bajaj", "Batra", "Anand", "Sood", "Sabharwal", "Kohli", "Gulati", "Puri", "Ahuja", "Bhardwaj", "Thakur", "Tomar", "Rathore", "Sisodia", "Solanki", "Chawla", "Khatri", "Nagpal", "Vohra", "Bhandari", "Kale", "Shinde", "More", "Jadhav", "Sawant", "Salunkhe", "Gaikwad", "Kadam", "Chavan", "Mohanty", "Behera", "Mahapatra", "Pradhan", "Dutta", "Paul", "Sen", "Kashyap", "Srivastava", "Mathur", "Nigam", "Pathak", "Rawat", "Biswas", "Pohekar", "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis", "Walker", "Hall", "Young", "King"]

street_types = ["MG Road", "Park Street", "Church Street", "Brigade Road", "Commercial Street", "Link Road", "Station Road", "College Road", "School Road", "Temple Road", "Main Road", "Market Road", "Airport Road", "Ring Road", "Outer Ring Road", "Inner Ring Road", "Residency Road", "Race Course Road", "Civil Lines", "Shivaji Road", "Nehru Road", "Gandhi Road", "Subhash Road", "Tilak Road", "Lal Bahadur Shastri Road", "Jawaharlal Nehru Road", "Ashok Nagar", "Green Park", "Rajendra Nagar", "Indira Nagar", "Vasant Vihar", "Model Town", "Patel Nagar", "Shastri Nagar", "Azad Nagar", "Krishna Nagar", "Saraswati Vihar", "Gokul Road", "Lake View Road", "Hill Road", "Beach Road", "Canal Road", "Fort Road", "High Court Road", "Bus Stand Road", "Railway Colony Road", "Industrial Area", "IT Park Road", "Sector 1", "Sector 5", "Sector 10", "Sector 12", "Sector 15", "Sector 18", "Sector 21", "Sector 28", "Sector 32", "Sector 45", "Sector 62", "Sector 63", "Sector 71", "Phase 1", "Phase 2", "Phase 3", "Old Market Road", "New Market Road", "University Road", "Medical College Road", "Collectorate Road", "Court Road", "Factory Road", "Mill Road", "Housing Board Colony", "Teachers Colony", "Officers Colony", "Police Line Road", "Garden Road", "Central Avenue", "Kingsway"]
cities = ["Delhi", "Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Bhopal", "Patna", "Ranchi", "Bhubaneswar", "Cuttack", "Visakhapatnam", "Vijayawada", "Guntur", "Mysuru", "Mangaluru", "Hubballi", "Belagavi", "Kochi", "Thiruvananthapuram", "Kozhikode", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli", "Vellore", "Surat", "Vadodara", "Rajkot", "Nashik", "Aurangabad", "Amravati", "Kolhapur", "Solapur", "Sangli", "Goa", "Panaji", "Agra", "Meerut", "Noida", "Greater Noida", "Ghaziabad", "Gurugram", "Faridabad", "Chandigarh", "Mohali", "Amritsar", "Ludhiana", "Jalandhar", "Shimla", "Dehradun", "Haridwar", "Varanasi", "Prayagraj", "Gorakhpur", "Bareilly", "Aligarh", "Mathura", "Khurja", "Alwar", "Udaipur", "Jodhpur", "Srinagar", "Jammu", "Siliguri", "Guwahati", "Shillong", "Imphal", "Aizawl", "Itanagar", "Gangtok", "Port Blair"]
localities = ["Indiranagar", "Koramangala", "Whitefield", "Electronic City", "HSR Layout", "JP Nagar", "Jayanagar", "BTM Layout", "Banashankari", "Malleshwaram", "Rajajinagar", "Hebbal", "Marathahalli", "Yelahanka", "Anna Nagar", "T. Nagar", "Adyar", "Velachery", "Tambaram", "Porur", "Nungambakkam", "Guindy", "Chromepet", "Mylapore", "Bandra", "Andheri", "Powai", "Borivali", "Dadar", "Colaba", "Chembur", "Ghatkopar", "Malad", "Vashi", "Nerul", "Aundh", "Hinjewadi", "Kothrud", "Baner", "Wakad", "Hadapsar", "Pimpri", "Chinchwad", "Nigdi", "Kharadi", "Salt Lake", "New Town", "Howrah", "Ballygunge", "Park Circus", "Aliganj", "Gomti Nagar", "Hazratganj", "Civil Lines", "Rajajipuram", "Vaishali", "Indirapuram", "Kaushambi", "Sector 62", "Sector 18", "Dwarka", "Rohini", "Saket", "Lajpat Nagar", "Karol Bagh", "Vasant Kunj", "Mayur Vihar", "Janakpuri", "Pitampura", "Malviya Nagar", "C Scheme", "Vaishali Nagar", "Mansarovar", "Civil Lines", "Shivaji Nagar", "Ashok Nagar", "Model Town", "Shastri Nagar", "Patel Nagar"]
states = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"]

sentence_templates_with_entity = [
    "My name is {PERSON_NAME}.", "I am {PERSON_NAME}.", "Please contact {PERSON_NAME} regarding this.", "You can reach out to {PERSON_NAME} for assistance.", "The meeting is with {PERSON_NAME}.", "Please ask {PERSON_NAME} to call me back.", "{PERSON_NAME} will attend the conference.", "{PERSON_NAME} has completed the assignment.", "The parcel belongs to {PERSON_NAME}.", "I received a message from {PERSON_NAME}.", "This document was signed by {PERSON_NAME}.",
    "{PERSON_NAME} is responsible for this project.", "Kindly forward this email to {PERSON_NAME}.", "The reservation is under the name {PERSON_NAME}.", "I spoke with {PERSON_NAME} yesterday.", "{PERSON_NAME} will arrive tomorrow morning.", "The interview is scheduled with {PERSON_NAME}.", "{PERSON_NAME} requested additional information.", "Our new manager is {PERSON_NAME}.", "Congratulations, {PERSON_NAME}!", "Dear {PERSON_NAME}, welcome aboard.",
    "Thank you, {PERSON_NAME}, for your support.", "Happy birthday, {PERSON_NAME}!", "Please remind {PERSON_NAME} about the meeting.", "The report was prepared by {PERSON_NAME}.", "{PERSON_NAME} submitted the application online.", "We are waiting for {PERSON_NAME}.", "{PERSON_NAME} has confirmed the booking.", "Please notify {PERSON_NAME} immediately.", "I met {PERSON_NAME} at the airport.", "This seat is reserved for {PERSON_NAME}.",
    "{PERSON_NAME} forgot their ID card.", "The customer is {PERSON_NAME}.", "Please verify the identity of {PERSON_NAME}.", "{PERSON_NAME} accepted the invitation.", "I have known {PERSON_NAME} for years.", "{PERSON_NAME} is the team leader.", "The award goes to {PERSON_NAME}.", "Could you introduce me to {PERSON_NAME}?", "{PERSON_NAME} left a voicemail.", "The account belongs to {PERSON_NAME}.",
    "{PERSON_NAME} canceled the appointment.", "Everyone appreciated {PERSON_NAME}'s presentation.", "The contract was reviewed by {PERSON_NAME}.", "Please send a copy to {PERSON_NAME}.", "{PERSON_NAME} reported the issue yesterday.", "The complaint was filed by {PERSON_NAME}.", "{PERSON_NAME} has a doctor's appointment today.", "We welcomed {PERSON_NAME} to the team.", "I shared the documents with {PERSON_NAME}.", "Ship the package to {ADDRESS}.", "The delivery address is {ADDRESS}.",
    "Please send the invoice to {ADDRESS}.", "The event will take place at {ADDRESS}.", "The customer lives at {ADDRESS}.", "Please update the address to {ADDRESS}.", "The courier is heading to {ADDRESS}.", "Meet me at {ADDRESS}.", "The office is located at {ADDRESS}.", "Our headquarters moved to {ADDRESS}.", "The package was delivered to {ADDRESS}.", "The cab is waiting at {ADDRESS}.",
    "Return the documents to {ADDRESS}.", "The invitation was mailed to {ADDRESS}.", "Navigate to {ADDRESS}.", "The warehouse is near {ADDRESS}.", "Please verify {ADDRESS} before shipping.", "The customer recently moved to {ADDRESS}.", "The restaurant is opposite {ADDRESS}.", "I left my bag at {ADDRESS}.", "The repair technician visited {ADDRESS}.", "Pickup is scheduled from {ADDRESS}.", "The hotel is located at {ADDRESS}.",
    "Please enter {ADDRESS} into the GPS.", "The apartment is at {ADDRESS}.", "Our branch operates from {ADDRESS}.", "The police arrived at {ADDRESS}.", "The ambulance was dispatched to {ADDRESS}.", "The property is registered at {ADDRESS}.", "The inspection took place at {ADDRESS}.", "{PERSON_NAME} lives at {ADDRESS}.", "{PERSON_NAME} recently moved to {ADDRESS}.", "Please deliver {PERSON_NAME}'s package to {ADDRESS}.", "{PERSON_NAME} works near {ADDRESS}.",
    "{PERSON_NAME} asked us to meet at {ADDRESS}.", "Dear {PERSON_NAME}, your order will arrive at {ADDRESS}.", "The parcel for {PERSON_NAME} was shipped to {ADDRESS}.", "{PERSON_NAME} confirmed that the correct address is {ADDRESS}.", "A letter addressed to {PERSON_NAME} was sent to {ADDRESS}.", "{PERSON_NAME} checked in from {ADDRESS}.", "{PERSON_NAME} registered with the address {ADDRESS}.", "Please ask {PERSON_NAME} to verify {ADDRESS}.", "The driver picked up {PERSON_NAME} from {ADDRESS}.", "{PERSON_NAME} requested delivery at {ADDRESS}.",
    "The appointment for {PERSON_NAME} is at {ADDRESS}.", "{PERSON_NAME} received the package at {ADDRESS}.", "Emergency services were called for {PERSON_NAME} at {ADDRESS}.", "{PERSON_NAME} left their belongings at {ADDRESS}.", "The invitation for {PERSON_NAME} was mailed to {ADDRESS}.", "{PERSON_NAME} scheduled a meeting at {ADDRESS}.", "{PERSON_NAME} owns a property at {ADDRESS}.", "Please confirm that {PERSON_NAME} resides at {ADDRESS}.", "{PERSON_NAME} signed the delivery receipt at {ADDRESS}.", "The courier called {PERSON_NAME} before reaching {ADDRESS}.", 
    "{PERSON_NAME} has been registered at {ADDRESS}.", "The maintenance team met {PERSON_NAME} at {ADDRESS}.", "{PERSON_NAME} updated their address to {ADDRESS}.", "The replacement package for {PERSON_NAME} will be sent to {ADDRESS}.", "{PERSON_NAME} requested a pickup from {ADDRESS}.", "The welcome kit for {PERSON_NAME} was delivered to {ADDRESS}."
]

sentence_templates_without_entity = [
    "The meeting is scheduled for 3 PM tomorrow.", "Please review the attached document.", "Thanks for your quick response.", "The weather looks good this weekend.", "I have completed the task.", "The report is ready for review.", "Your request has been processed.", "The payment was received successfully.", "Please try again later.", "The application has been approved.",
    "The server is currently unavailable.", "We appreciate your patience.", "The event starts at 10 AM.", "Lunch will be served at noon.", "The train arrived on time.", "The flight has been delayed.", "The package has been dispatched.", "Your order is out for delivery.", "The deadline has been extended.", "Please save your work frequently.",
    "The internet connection is stable.", "The printer is out of paper.", "Your password has been updated.", "Please restart your computer.", "The download has finished.", "The upload failed unexpectedly.", "A new update is available.", "The installation completed successfully.", "The battery is fully charged.", "Please check your email inbox.",
    "The conference begins next Monday.", "Dinner will be ready soon.", "The room has been cleaned.", "The lights are turned off.", "Please close the window.", "The door is locked.", "The exam begins at 9 AM.", "The classroom is on the second floor.", "Coffee is available in the kitchen.", "The presentation went well.",
    "Everyone enjoyed the event.", "The movie starts in twenty minutes.", "Today's traffic is unusually heavy.", "The store closes at 9 PM.", "The library opens at 8 AM.", "Breakfast is included with your stay.", "The reservation has been confirmed.", "Please wait for further instructions.", "The issue has been resolved.", "The system is running normally.",
    "The file has been deleted.", "The backup completed overnight.", "Your subscription has expired.", "The session timed out.", "The website is under maintenance.", "The form was submitted successfully.", "Please enter a valid password.", "The verification code has expired.", "Your profile has been updated.", "No further action is required.",
    "The process completed successfully.", "The package arrived earlier than expected.", "The invoice has been generated.", "Your appointment has been confirmed.", "The workshop was very informative.", "The restaurant was fully booked.", "The bus leaves every thirty minutes.", "The elevator is temporarily out of service.", "The road is closed for repairs.", "The park is open until sunset.",
    "The museum is closed on Mondays.", "The concert was sold out.", "The hotel offers free Wi-Fi.", "The food was delicious.", "The coffee is still hot.", "The flowers are blooming.", "The garden looks beautiful.", "The children are playing outside.", "The cat is sleeping on the sofa.", "The dog is waiting by the door.",
    "It started raining suddenly.", "The sky is completely clear today.", "The air feels fresh this morning.", "The book is available online.", "The assignment was submitted on time.", "The results will be announced tomorrow.", "The project is progressing well.", "The experiment produced consistent results.", "Everything is working as expected.", "The software crashed unexpectedly.",
    "The network connection was restored.", "The application is running smoothly.", "The queue is moving quickly.", "The shopping cart is empty.", "The checkout process is simple.", "The package requires a signature.", "The document has been archived.", "The camera battery is low.", "The microphone is muted.", "The speaker volume is too high."
]

def generate_address():
    house_no = random.randint(1, 999)
    street = random.choice(street_types)
    locality = random.choice(localities)
    city = random.choice(cities)
    state = random.choice(states)
    pincode = random.randint(100000, 999999)

    formats = [
        f"{house_no}, {street}, {locality}, {city}, {state} {pincode}",
        f"{house_no}, {street}, {locality}, {city} - {pincode}",
        f"{street}, {locality}, {city}, {state}",
        f"{house_no}, {locality}, {city}",
        f"{street}, {city}, {state} {pincode}",
        f"{locality}, {city}, {state}",
    ]
    return random.choice(formats)


def generate_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_example():
    use_entity = random.random() < 0.65  # ~65% positive examples, 35% negative

    if not use_entity:
        text = random.choice(sentence_templates_without_entity)
        return text, []

    template = random.choice(sentence_templates_with_entity)
    entities = []
    text = template

    if "{PERSON_NAME}" in text and "{ADDRESS}" in text:

        name = generate_name()
        addr = generate_address()
        
        text = text.replace("{PERSON_NAME}", name, 1)
        name_start = text.index(name)
        entities.append((name_start, name_start + len(name), "PERSON_NAME"))

        text = text.replace("{ADDRESS}", addr, 1)
        addr_start = text.index(addr)
        entities.append((addr_start, addr_start + len(addr), "ADDRESS"))

    elif "{PERSON_NAME}" in text:
        name = generate_name()
        text = text.replace("{PERSON_NAME}", name, 1)
        name_start = text.index(name)
        entities.append((name_start, name_start + len(name), "PERSON_NAME"))

    elif "{ADDRESS}" in text:
        addr = generate_address()
        text = text.replace("{ADDRESS}", addr, 1)
        addr_start = text.index(addr)
        entities.append((addr_start, addr_start + len(addr), "ADDRESS"))

    return text, entities


def generate_dataset(n_examples=7500):
    dataset = []
    seen = set()
    attempts = 0
    while len(dataset) < n_examples and attempts < n_examples * 3:
        attempts += 1
        text, entities = generate_example()
        if text in seen: 
            continue
        seen.add(text)
        dataset.append({"text": text, "entities": entities})
    return dataset


dataset = generate_dataset(7500)
print(f"Generated {len(dataset)} examples")
print(dataset[0])
print(dataset[1])