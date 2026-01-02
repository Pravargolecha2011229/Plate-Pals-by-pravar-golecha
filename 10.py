import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from User_Data import UserDataManager
import time
import asyncio
from concurrent.futures import TimeoutError
from urllib.parse import quote

ACHIEVEMENTS = {
    "recipe_achievements": [
        {"name": "Recipe Rookie", "requirement": 15, "points": 25, "description": "Generate 15 recipes"},
        {"name": "Recipe Master", "requirement": 45, "points": 50, "description": "Generate 45 recipes"},
        {"name": "Recipe Chef", "requirement": 95, "points": 75, "description": "Generate 95 recipes"}
    ],
    "leftover_achievements": [
        {"name": "Waste Warrior", "requirement": 15, "points": 25, "description": "Manage 15 leftover items"},
        {"name": "Sustainability Star", "requirement": 75, "points": 50, "description": "Manage 45 leftover items"},
        {"name": "Zero Waste Hero", "requirement": 180, "points": 75, "description": "Manage 95 leftover items"}
    ],
    "quiz_achievements": [
        {"name": "Quiz Novice", "requirement": 15, "points": 25, "description": "Answer 5 quiz questions correctly"},
        {"name": "Quiz Expert", "requirement": 25, "points": 50, "description": "Answer 15 quiz questions correctly"},
        {"name": "Quiz Master", "requirement": 50, "points": 100, "description": "Answer 30 quiz questions correctly"},
        {"name": "Perfect Streak", "requirement": 5, "points": 50, "description": "Get 5 correct answers in a row"},
        {"name": "Quiz Champion", "requirement": 750, "points": 150, "description": "Achieve 90 percent accuracy in 50 questions"}
    ],
    "beverage_achievements": [
        {"name": "Beverage Beginner", "requirement": 15, "points": 25, "description": "Create 5 beverage recipes"},
        {"name": "Mixology Master", "requirement": 25, "points": 50, "description": "Create 15 beverage recipes"},
        {"name": "Drink Designer", "requirement": 50, "points": 75, "description": "Create 30 beverage recipes"},
        {"name": "Seasonal Specialist", "requirement": 70, "points": 100, "description": "Create beverages for all seasons"},
        {"name": "Healthy Hydration", "requirement": 100, "points": 150, "description": "Create 30 sugar-free beverages"}
    ],
   "dessert_achievements": [
        {"name": "Sweet Beginner", "requirement": 15, "points": 25, "description": "Create 5 dessert recipes"},
        {"name": "Pastry Chef", "requirement": 25, "points": 50, "description": "Create 15 dessert recipes"},
        {"name": "Dessert Artist", "requirement": 50, "points": 75, "description": "Create 30 dessert recipes"},
        {"name": "Global Sweet Master", "requirement": 70, "points": 100, "description": "Create desserts from 5 different cuisines"},
        {"name": "Healthy Sweet Maker", "requirement": 100, "points": 150, "description": "Create 10 sugar-free desserts"}
    ]
}

# Page configuration
st.set_page_config(
    page_title="Plate Pals - Smart Restaurant Management",
    page_icon="🍽️",
    layout="wide"
)

# Top banner for improved UI
try:
    st.markdown(
        "<div style='text-align:center'>\n" 
        "<h1 style='margin:0'>🍽️ PlatePals</h1>\n"
        "<p style='margin:0;color:gray'>Serve Smart. Waste Less. Know More.</p>\n"
        "</div>",
        unsafe_allow_html=True,
    )
except Exception:
    # If the environment doesn't allow unsafe HTML, fall back to simple title
    st.title("🍽️ PlatePals - Smart Restaurant Management")

# Configure Gemini API
# Load Gemini API key from Streamlit secrets or fallback to streamlit/secrets.toml
GEMINI_API_KEY = None
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
except Exception:
    GEMINI_API_KEY = None

# If user placed secrets in a non-dot folder named 'streamlit', attempt to read it
if not GEMINI_API_KEY:
    try:
        import os
        try:
            import tomllib as toml_lib  # Python 3.11+
        except Exception:
            try:
                import toml as toml_lib  # fallback if package installed
            except Exception:
                toml_lib = None

        alt_path = os.path.join(os.getcwd(), "streamlit", "secrets.toml")
        if os.path.exists(alt_path) and toml_lib:
            with open(alt_path, "rb") as f:
                # tomllib requires bytes, toml package accepts str
                parsed = toml_lib.loads(f.read().decode() if hasattr(f.read, '__call__') else f.read())
                # normalize parsed depending on parser
                if isinstance(parsed, dict):
                    GEMINI_API_KEY = parsed.get("GEMINI_API_KEY") or parsed.get("gemini_api_key")
    except Exception:
        GEMINI_API_KEY = None

if not GEMINI_API_KEY:
    st.error("Gemini API key not found. Add `GEMINI_API_KEY` to .streamlit/secrets.toml or streamlit/secrets.toml")
else:
    genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 5000,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]
    )
except Exception as e:
    st.error(f"Error initializing model: {str(e)}")


# Quiz Questions Database
COOKING_QUIZ = [
    {
        "question": "What temperature is considered safe for cooking chicken?",
        "options": ["145Â°F", "165Â°F", "175Â°F", "185Â°F"],
        "correct": "165Â°F"
    },
    {
        "question": "Which herb is commonly used in Italian cuisine?",
        "options": ["Basil", "Lemongrass", "Cumin", "Cardamom"],
        "correct": "Basil"
    },
    {
        "question": "What is the main ingredient in traditional guacamole?",
        "options": ["Tomatoes", "Avocado", "Onions", "Lime"],
        "correct": "Avocado"
    },
    {
        "question": "Which cooking method involves cooking food in hot oil?",
        "options": ["Braising", "Steaming", "Frying", "Roasting"],
        "correct": "Frying"
    },
    {
        "question": "What is the process of partially cooking food in boiling water and then quickly cooling it in ice water?",
        "options": ["SautÃ©ing", "Blanching", " Braising", "Roasting"],
        "correct": "Blanching"
    },
    {
        "question": "Which ingredient makes baked goods rise?",
        "options": ["Sugar", "Flour", "Salt", "Baking soda"],
        "correct": "Baking soda"
    },
   {
        "question": "What does 'tempering' mean when working with chocolate?",
        "options": ["Heating and cooling chocolate to stabilize it", " Mixing chocolate with milk", "Melting chocolate over direct heat", " Adding sugar to chocolate"],
        "correct": "Heating and cooling chocolate to stabilize it"
    },
    {
        "question": "Which country is known for originating sushi?",
        "options": ["China", "Korea", "Japan","Thailand"],
        "correct": "Japan"
    },
    {
        "question": "What is the main ingredient in hummus?",
        "options": ["Lentils", "Chickpeas", "Black beans","Peanuts"],
        "correct": "Chickpeas"
    },
    {
        "question": "What does 'sous vide' mean in cooking?",
        "options": ["Cooking with steam", "Cooking food in a vaccum-sealed bag in water", "Cooking over an open flame","Cooking in a pressure cooker"],
        "correct": "Cooking food in a vaccum-sealed bag in water"
    },
    {
        "question": "Which kitchen tool is best for zesting a lemon?",
        "options": ["Knife", "Peeler", "Grater","Microplane"],
        "correct": "Microplane"        
    },
    {
        "question": "What is the purpose of deglazing a pan?",
        "options": ["To remove excess fat", "To dissolve browned bits for added flavor", "To cool down the pan","To thicken a sauce"],
        "correct": " To dissolve browned bits for added flavor"        
    },
    {
        "question": "What does the term 'al dente' mean when cooking pasta?",
        "options": ["Soft and mushy", "Firm to the bite", "Overcooked","Undercooked"],
        "correct": "Firm to the bite"        
    },
    {
        "question": "What is the purpose of resting meat after cooking?",
        "options": ["To cool it down quickly", "To allow juices to redistribute", " To make it easier to cut","To enhance the flavor"],
        "correct": "To allow juices to redistribute"        
    },
    {
        "question": "What does the term 'proofing' mean in baking?",
        "options": ["Checking for quality", " Baking at a low temperature", "Mixing ingredients together","Allowing dough to rise"],
        "correct": "Allowing dough to rise"         
    },
    {
        "question": "What type of sugar is commonly used in making caramel?",
        "options": ["Brown sugar", "Powdered sugar", "Granulated sugar","Coconut sugar"],
        "correct": "Granulated sugar"        
    },
    {
        "question": "Which type of rice is used to make sushi?",
        "options": ["Basmati rice", "Jasmine rice", "Arborio rice","Short-grain rice"],
        "correct": "Short-grain rice"        
    },
    {
        "question": "Which spice is commonly used in Indian cuisine and gives curry its yellow color?",
        "options": ["Saffron", "Paprika", "Turmeric","Cumin"],
        "correct": "Turmeric"        
    },
    {
        "question": "What is the purpose of 'searing' meat?",
        "options": ["To cook it completely", "To keep it cold", "To remove fat","To create a flavorful crust"],
        "correct": "To create a flavorful crust"        
    },
    {
        "question": "What is the French cooking term for 'everything in its place' (organizing ingredients before cooking)?",
        "options": ["Mise en place", "Sous vide", "En papillote","Bain-marie"],
        "correct": "Mise en place"        
    },
    {
        "question": "Which cooking method involves cooking food slowly in a covered pot with a small amount of liquid?",
        "options": ["Braising", "SautÃ©ing", "Boiling","Grilling"],
        "correct": "Braising"        
    },
    {
        "question": "What gas is released when baking soda reacts with an acid?",
        "options": ["Oxygen", "Carbon dioxide", "Hydrogen","Nitrogen"],
        "correct": "Carbon dioxide"        
    },
    {
        "question": "What is the main ingredient in a traditional crÃ¨me brÃ»lÃ©e?",
        "options": ["Flour", "Cream", "Cheese","Butter"],
        "correct": "Cream"        
    },
    {
        "question": "What is the traditional flatbread of Mexico called?",
        "options": ["Tortilla", "Naam", "Roti","Bhature","Pita"],
        "correct": "Tortilla"        
    },
    {
        "question": "Which dish is traditionally made with fermented cabbage?",
        "options": ["Kimchi", "Sushi", "Falafel","Pasta"],
        "correct": "Kimchi"        
    },
    {
        "question": "What is the primary ingredient in a classic French bÃ©chamel sauce?",
        "options": ["Milk", "Cream", "Cheese","Butter"],
        "correct": "Milk"        
    },
    {
        "question": "What does 'basting' mean in cooking?",
        "options": ["Cooking with dry heat", "Pouring juices or melted fat over food while cooking", "Cooking food in a water bath","Cutting food into small pieces"],
        "correct": "Pouring juices or melted fat over food while cooking"        
    },
    {
        "question": "What is the term for cooking food in a tightly sealed pouch, usually with parchment paper or foil?",
        "options": ["En papillote", "Roasting", "Poaching","Braising"],
        "correct": "En papillote"        
    },
    {
        "question": "Which tool is best for checking the internal temperature of Water?",
        "options": ["Your hand", "Knife", "Tongs","Thermometer"],
        "correct": "Thermometer"        
    },
    {
        "question": "What is the best way to cut an onion without crying?",
        "options": ["Freeze the onion before cutting", "Use a dull knife", "Cut it under running water","Wear goggles"],
        "correct": "Freeze the onion before cutting"        
    },
    {
        "question": "Which of these dishes is traditionally cooked in a tandoor?",
        "options": ["Tacos", "Paella", "Naan","Sushi"],
        "correct": "Naan"        
    },
    {
        "question": "Which type of lentils are used to make traditional dal makhani?",
        "options": ["Moong dal", "Chana dal", "Masoor dal","Urad dal"],
        "correct": "Urad dal"    
    },
    {
        "question": "What spice gives biryani its distinctive yellow color?",
        "options": ["Saffron", "Turmeric", "Cumin","Spinach"],
        "correct": "Saffron"    
    },
    {
        "question": "What is the key ingredient in a traditional South Indian sambar?",
        "options": ["Chana dal", "Toor dal", "Rajma","Urad dal"],
        "correct": "Toor dal"    
    },
    {
        "question": "Which spice blend is commonly used in Indian chaat dishes?",
        "options": ["Garam Masala", "Chat Masala", "Rajma","Rasam Powder"],
        "correct": "Chat Masala"
    },
    {
        "question": "Which Indian dessert is made by deep-frying balls of khoya and soaking them in sugar syrup?",
        "options": ["Rasgulla", "Jalebi", "Barfi","Gulab Jamun"],
        "correct": "Gulab Jamun"
    },
    {
        "question": "Which spice is commonly known as 'Indian saffron' because of its color and use in Indian cuisine?",
        "options": ["Cardamom", "Turmeric", "Cumin","Mustard seeds"],
        "correct": "Turmeric"
    },
    {
        "question": "Which rice variety is most commonly used for making biryani?",
        "options": ["Jasmine rice", "Brown rice", "Basmati rice","Arborio rice"],
        "correct": "Basmati rice"
    },
    {
        "question": "What is the primary ingredient in traditional Punjabi lassi?",
        "options": ["Coconut milk", "Yogurt", "Condensed milk","Buttermilk"],
        "correct": "Yogurt"
    },
    {
        "question": "Which street food dish consists of hollow, crispy puris filled with spicy and tangy water?",
        "options": ["Dahi Puri", "Bhel Puri", "Pani Puri","Buttermilk"],
        "correct": "Pani Puri"
    }

]

# Initialize session state

if "last_gemini_call" not in st.session_state:
    st.session_state.last_gemini_call = 0

if 'generated_recipe' not in st.session_state:
    st.session_state.generated_recipe = None

if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserDataManager()


if 'recipe_database' not in st.session_state:
    menu_items = [
        {"day": "Monday", "dish": "Quinoa Salad Bowl", "ingredients": ["quinoa", "cucumber", "tomatoes", "feta cheese"], "feedback": 4.7},
        {"day": "Monday", "dish": "Grilled Chicken", "ingredients": ["chicken breast", "lemon", "herbs", "olive oil"], "feedback": 4.8},
        {"day": "Tuesday", "dish": "Mango Smoothie Bowl", "ingredients": ["mango", "banana", "almond milk", "chia seeds"], "feedback": 4.6},
        {"day": "Tuesday", "dish": "Mediterranean Wrap", "ingredients": ["wrap", "hummus", "vegetables", "feta"], "feedback": 4.5},
        {"day": "Wednesday", "dish": "Avocado Toast", "ingredients": ["bread", "avocado", "tomatoes", "microgreens"], "feedback": 4.7},
        {"day": "Wednesday", "dish": "Grilled Salmon", "ingredients": ["salmon", "lemon", "dill", "olive oil"], "feedback": 4.9},
    ]
    st.session_state.recipe_database = pd.DataFrame(menu_items)

if 'inventory' not in st.session_state:
    st.session_state.inventory = {
        "vegetables": ["spinach", "kale", "carrots", "bell peppers", "cucumber", "tomatoes"],
        "proteins": ["chicken breast", "salmon", "tofu", "eggs", "chickpeas"],
        "grains": ["quinoa", "brown rice", "bread", "oats"],
        "fruits": ["apples", "bananas", "berries", "mango", "avocado", "lemon"]
    }

if 'leftovers' not in st.session_state:
    st.session_state.leftovers = ["spinach", "quinoa", "tomatoes"]

if 'user_points' not in st.session_state:
    st.session_state.user_points = 0

if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []

if 'events' not in st.session_state:
    st.session_state.events = [
        {
            "name": "Corporate Lunch",
            "date": "2024-03-20",
            "guests": 50,
            "theme": "Mediterranean",
            "dietary_restrictions": ["Vegetarian", "Gluten-Free"],
            "status": "Upcoming"
        }
    ]    

def check_login_required():
    """Check if user is logged in, if not show login page"""
    if not st.session_state.current_user:
        st.title("🍽️ Welcome to PlatePals")
        st.write("Please login or sign up to continue")
        
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
        
        with login_tab:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                success, message = st.session_state.user_manager.verify_user(username, password)
                if success:
                    st.session_state.current_user = username
                    st.session_state.users = st.session_state.user_manager.users
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        with signup_tab:
            new_username = st.text_input("Username", key="signup_user")
            new_password = st.text_input("Password", type="password", key="signup_pass")
            if st.button("Sign Up"):
                success, message = st.session_state.user_manager.add_user(new_username, new_password)
                if success:
                    st.session_state.current_user = new_username
                    st.session_state.users = st.session_state.user_manager.users
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        st.stop()


if 'users' not in st.session_state:
    st.session_state.users = {}

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Helper Functions
def generate_recipe_with_timeout(prompt, timeout=60):
    try:
        with st.spinner("⏳ Generating your recipe..."):
            progress_bar = st.progress(0)
            progress_text = st.empty()

            # Simulated progress (UI only, no extra API calls)
            for progress in range(0, 90, 5):
                progress_bar.progress(progress)
                progress_text.text(f"Processing... {progress}%")
                time.sleep(0.2)

            # SINGLE Gemini API call (THIS IS THE FIX)
            recipe = model.generate_content(prompt).text

            progress_bar.progress(100)
            progress_text.text("Recipe generated successfully!")

            return recipe

    except Exception as e:
        # Cleanup UI
        try:
            progress_bar.empty()
            progress_text.empty()
        except:
            pass

        # Handle quota errors explicitly
        if "429" in str(e) or "ResourceExhausted" in str(e):
            st.error(" API limit reached. Please wait a few seconds and try again.")
        elif "Timeout" in str(e):
            st.error("âš ï¸ Recipe generation timed out. Please try again.")
        else:
            st.error(f"âŒ Error generating recipe: {str(e)}")

        return None



def get_recipe_from_gemini(ingredients, dietary_restrictions=None):
    """Generate recipe using Gemini API"""
    prompt = f"Create a detailed recipe using these ingredients also give the recipe properly including each and every detail of it also do not skip any mention or part of the recipe: {', '.join(ingredients)}"
    if dietary_restrictions:
        prompt += f"\nDietary restrictions: {', '.join(dietary_restrictions)}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating recipe: {str(e)}")
        return None

def add_points(points, reason):
    """Add points and log activity for the current user"""
    user = st.session_state.users[st.session_state.current_user]
    user['points'] += points
    user['activity_log'].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": reason,
        "points": points
    })
    st.session_state.user_manager.update_user_data(st.session_state.current_user, user)
def search_ingredients(search_term: str, ingredients_list: list) -> list:
    """Enhanced ingredient search with flexible matching and custom additions"""
    if not search_term:
        return ingredients_list

    search_term = search_term.lower()
    
    # Add searched term if not in list
    if search_term not in [i.lower() for i in ingredients_list]:
        ingredients_list.append(search_term.title())
    
    # Search with flexible matching
    matches = [
        item for item in ingredients_list 
        if search_term in item.lower() or 
        item.lower() in search_term or 
        any(word in item.lower() for word in search_term.split())
    ]
    
    return matches or [search_term.title()]

def get_all_ingredients():
    """Get all available ingredients across categories"""
    all_ingredients = []
    for category_items in st.session_state.inventory.values():
        all_ingredients.extend(category_items)
    return list(set(all_ingredients))

def suggest_recipes(ingredients, dietary_restrictions=None):
    """Generate recipe suggestions with enhanced prompting"""
    prompt = f"""Create a detailed recipe using these ingredients: {', '.join(ingredients)}
    Please include:
    - Recipe name
    - Preparation time
    - Cooking time
    - Difficulty level
    - Step by step instructions
    - Additional ingredients needed (if any)
    """
    if dietary_restrictions:
        prompt += f"\nMust be suitable for: {', '.join(dietary_restrictions)}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating recipe: {str(e)}")
        return None


def get_user_mentions():
    with st.expander("📖 Special Mentions", expanded=False):
        wants = st.text_area(
            "What do you want in the recipe?",
            placeholder="Example: Extra spicy, More gravy, Crispy texture, Quick to make, etc.",
            help="Mention specific things you want in your recipe"
        )
        
        dont_wants = st.text_area(
            "What do you NOT want in the recipe?",
            placeholder="Example: No garlic, Less oil, Not too sweet, No deep frying, etc.",
            help="Mention specific things you want to avoid in your recipe"
        )
        
        additional_notes = st.text_area(
            "Additional Notes",
            placeholder="Example: Family recipe preferences, Special occasions, Time constraints, etc.",
            help="Any other special instructions or preferences"
        )
        
        return {
            "wants": wants,
            "dont_wants": dont_wants,
            "additional_notes": additional_notes
        }




def check_achievements(user_data, achievement_type):
    """Check and award achievements"""
    if 'achievements' not in user_data:
        user_data['achievements'] = []

    if achievement_type == "dessert":
        dessert_recipes = [recipe for recipe in user_data.get('created_recipes', []) 
                         if recipe.get('type') == 'dessert']
        count = len(dessert_recipes)
        
        # Check dessert achievements
        for achievement in ACHIEVEMENTS['dessert_achievements']:
            if achievement['name'] not in [a['name'] for a in user_data['achievements']]:
                if "sugar-free" in achievement['description'].lower():
                    sugar_free_count = len([r for r in dessert_recipes 
                                        if 'Sugar-Free' in r.get('dietary_restrictions', [])])
                    if sugar_free_count >= achievement['requirement']:
                        award_achievement(user_data, achievement)
                elif "different cuisines" in achievement['description'].lower():
                    unique_cuisines = len(set(recipe.get('cuisine', '') 
                                        for recipe in dessert_recipes))
                    if unique_cuisines >= 5:
                        award_achievement(user_data, achievement)
                elif count >= achievement['requirement']:
                    award_achievement(user_data, achievement)
        return

    elif achievement_type == "beverage":
        beverage_recipes = [recipe for recipe in user_data.get('created_recipes', []) 
                          if recipe.get('type') == 'beverage']
        count = len(beverage_recipes)
        
        # Check beverage achievements
        for achievement in ACHIEVEMENTS['beverage_achievements']:
            if achievement['name'] not in [a['name'] for a in user_data['achievements']]:
                if "sugar-free" in achievement['description'].lower():
                    sugar_free_count = len([r for r in beverage_recipes 
                                          if 'Sugar-Free' in r.get('dietary_restrictions', [])])
                    if sugar_free_count >= achievement['requirement']:
                        award_achievement(user_data, achievement)
                elif "all seasons" in achievement['description'].lower():
                    seasons = set(recipe.get('season', '') for recipe in beverage_recipes)
                    if len(seasons & {'Summer', 'Winter', 'Spring', 'Fall'}) == 4:
                        award_achievement(user_data, achievement)
                elif count >= achievement['requirement']:
                    award_achievement(user_data, achievement)
        return

    elif achievement_type == "recipe":
        count = len(user_data.get('created_recipes', []))
        achievements = ACHIEVEMENTS['recipe_achievements']
    
    elif achievement_type == "leftover":
        count = len(user_data.get('leftover_ingredients', []))
        achievements = ACHIEVEMENTS['leftover_achievements']
    
    elif achievement_type == "quiz":
        quiz_stats = user_data.get('quiz_stats', {})
        correct_answers = quiz_stats.get('correct_answers', 0)
        total_attempts = quiz_stats.get('total_attempts', 0)
        accuracy = (correct_answers / total_attempts * 100) if total_attempts > 0 else 0
        
        # Check quiz achievements
        for achievement in ACHIEVEMENTS['quiz_achievements']:
            if achievement['name'] not in [a['name'] for a in user_data['achievements']]:
                if "correct answers" in achievement['description']:
                    if correct_answers >= achievement['requirement']:
                        award_achievement(user_data, achievement)
                elif "accuracy" in achievement['description']:
                    if total_attempts >= achievement['requirement'] and accuracy >= 90:
                        award_achievement(user_data, achievement)
                elif "streak" in achievement['description']:
                    current_streak = user_data.get('current_streak', 0)
                    if current_streak >= achievement['requirement']:
                        award_achievement(user_data, achievement)
        return

    # Check regular achievements for recipe and leftover types
    if 'achievements' in ACHIEVEMENTS:
        for achievement in achievements:
            if (achievement['name'] not in [a['name'] for a in user_data['achievements']] and 
                count >= achievement['requirement']):
                award_achievement(user_data, achievement)

def award_achievement(user_data, achievement):
    """Helper function to award achievements"""
    user_data['achievements'].append({
        'name': achievement['name'],
        'earned_on': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'description': achievement['description']
    })
    add_points(achievement['points'], f"Achievement unlocked: {achievement['name']}")
    st.balloons()
    st.success(f"🏆 Achievement Unlocked: {achievement['name']}! +{achievement['points']} points")



# Sidebar
def show_sidebar():
    st.sidebar.title("🍽️ PlatePals")
    st.sidebar.header("Serve Smart. Waste Less. Know More.")

    # User info
    user = st.session_state.users[st.session_state.current_user]
    st.sidebar.write(f"Welcome, {st.session_state.current_user}!")
    st.sidebar.metric("🏆 Points", user['points'])
    
    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.rerun()

    return st.sidebar.selectbox(
        "Select Feature", 
        ["Dashboard", "Profile", "Search", "Recipe Suggestions", "Leftover Management", 
         "Menu Personalization", "Event Manager", "Cooking Quiz", "Beverage Generator", "Dessert Generator"]
    )


# Main Content
def show_user_profile(user_data):
    st.title(f"👤 {st.session_state.current_user}'s Profile")
    
    # Profile Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Points", user_data['points'])
    with col2:
        st.metric("Quiz Attempts", user_data['quiz_stats']['total_attempts'])
    with col3:
        accuracy = 0 if user_data['quiz_stats']['total_attempts'] == 0 else \
                  (user_data['quiz_stats']['correct_answers'] / user_data['quiz_stats']['total_attempts']) * 100
        st.metric("Quiz Accuracy", f"{accuracy:.1f}%")
    
    # Progress Tracking
    tabs = st.tabs(["Activity Log", "Recipes", "Events", "Quiz Progress", "Leftovers", "Achievements", "Friends & Leaderboard", "Beverages", "Desserts"])
    
    with tabs[0]:
        st.subheader("📊 Activity History")
        if user_data['activity_log']:
            df = pd.DataFrame(user_data['activity_log'])
            st.dataframe(df, hide_index=True)
            
            # Points Timeline
            fig = px.line(df, x='date', y='points', title='Points Timeline')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity recorded yet")

  
    with tabs[1]:
      st.subheader(" Created Recipes")
      # Filter to show only recipes from Recipe Suggestions
      suggested_recipes = [recipe for recipe in user_data['created_recipes'] 
                        if 'type' not in recipe]  # Recipes without type are from Recipe Suggestions
    
      if suggested_recipes:
        for recipe in suggested_recipes:
            with st.expander(f"{recipe['date']} - {recipe['name']}"):
                st.write("**Ingredients used:**")
                st.write(", ".join(recipe['ingredients']))
                st.write("**Recipe details:**")
                st.write(recipe['details'])
      else:
        st.info("No recipes created yet. Try the Recipe Suggestions feature!")

    with tabs[2]:
        st.subheader("🎉 Events")
        if user_data['completed_events']:
            for event in user_data['completed_events']:
                with st.expander(f"{event['date']} - {event['name']}"):
                    st.write(f"**Theme:** {event['theme']}")
                    st.write(f"**Guests:** {event['guests']}")
                    st.write(f"**Status:** {event['status']}")
                    if 'menu' in event:
                        st.write("**Menu:**")
                        for course, items in event['menu'].items():
                            if items.strip():
                                st.write(f"*{course}:* {items}")
        else:
            st.info("No events created yet")
    
    with tabs[3]:
        st.subheader(" Quiz Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Questions Attempted", 
                     user_data['quiz_stats']['total_attempts'])
        with col2:
            st.metric("Correct Answers", 
                     user_data['quiz_stats']['correct_answers'])
    
    with tabs[4]:  # Leftovers tab
     st.subheader("â™»ï¸ Leftover Management History")
     if user_data.get('leftovers'):
        # Display all leftover recipes
        for recipe in user_data['leftovers']:
            with st.expander(f"{recipe['date']} - {recipe['name']}"):
                # Recipe Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("** Ingredients Used:**")
                    for ingredient in recipe['ingredients']:
                        st.write(f"- {ingredient['name']} ({ingredient['quantity']}g) - {ingredient['type']}")
                    
                    st.write("**â²ï¸ Cooking Information:**")
                    st.write(f"- Meal Type: {recipe['meal_type']}")
                    st.write(f"- Cooking Time: {recipe['cooking_time']} minutes")
                    st.write(f"- Difficulty Level: {recipe['difficulty']}")
                
                with col2:
                    st.write("**📖 Recipe Details:**")
                    st.write(f"- Target Calories: {recipe['calories']} kcal")
                    if recipe.get('dietary_prefs'):
                        st.write("** Dietary Preferences:**")
                        for pref in recipe['dietary_prefs']:
                            st.write(f"- {pref}")
                
                # Full Recipe
                st.write("**📖 Complete Recipe:**")
                st.write(recipe['recipe'])
     else:
        st.info("No leftover recipes created yet. Try the Leftover Management feature!")

    with tabs[5]:  # Achievements tab
      st.subheader("🏆 Achievements")
      if 'achievements' in user_data and user_data['achievements']:
        for achievement in user_data['achievements']:
            with st.expander(f"🏆 {achievement['name']}"):
                st.write(f"**Description:** {achievement['description']}")
                st.write(f"**Earned on:** {achievement['earned_on']}")
      else:
        st.info("No achievements unlocked yet. Keep using the app to earn achievements!")
    
      # Show available achievements
      st.subheader("Available Achievements")
      col1, col2 = st.columns(2)
    
      # Column 1: Recipe and Dessert Achievements
      with col1:
        st.write("**🍰 Recipe Achievements**")
        for achievement in ACHIEVEMENTS['recipe_achievements']:
            earned = 'achievements' in user_data and any(a['name'] == achievement['name'] for a in user_data['achievements'])
            st.write(f"{'âœ…' if earned else 'â­•'} {achievement['name']}: {achievement['description']}")
        
        st.write("")  # Add spacing
        st.write("**🍰 Dessert Achievements**")
        for achievement in ACHIEVEMENTS['dessert_achievements']:
            earned = 'achievements' in user_data and any(a['name'] == achievement['name'] for a in user_data['achievements'])
            st.write(f"{'âœ…' if earned else 'â­•'} {achievement['name']}: {achievement['description']}")
    
      # Column 2: Leftover and Beverage Achievements
      with col2:
        st.write("**â™»ï¸ Leftover Management Achievements**")
        for achievement in ACHIEVEMENTS['leftover_achievements']:
            earned = 'achievements' in user_data and any(a['name'] == achievement['name'] for a in user_data['achievements'])
            st.write(f"{'âœ…' if earned else 'â­•'} {achievement['name']}: {achievement['description']}")
        
        st.write("")  # Add spacing
        st.write("**🍹 Beverage Achievements**")
        for achievement in ACHIEVEMENTS['beverage_achievements']:
            earned = 'achievements' in user_data and any(a['name'] == achievement['name'] for a in user_data['achievements'])
            st.write(f"{'âœ…' if earned else 'â­•'} {achievement['name']}: {achievement['description']}")
    
    with tabs[6]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Friends")
            # Add friend section
            new_friend = st.text_input("Add Friend (username)")
            if st.button("Add Friend"):
                success, message = st.session_state.user_manager.add_friend(
                    st.session_state.current_user, new_friend)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            
            # Display friends list
            st.write("**Your Friends**")
            if 'friends' in user_data and user_data['friends']:
                for friend in user_data['friends']:
                    with st.expander(friend):
                        friend_data = st.session_state.user_manager.users.get(friend, {})
                        st.write(f"Points: {friend_data.get('points', 0)}")
                        st.write(f"Achievements: {len(friend_data.get('achievements', []))}")
            else:
                st.info("No friends added yet")
        
        with col2:
            st.subheader("🏆 Leaderboard")
            leaderboard = st.session_state.user_manager.get_leaderboard()
            
            # Create leaderboard table
            leaderboard_df = pd.DataFrame(leaderboard)
            st.dataframe(
                leaderboard_df,
                hide_index=True,
                column_config={
                    'username': 'Player',
                    'points': st.column_config.NumberColumn('Points', format='%d 🏆'),
                    'achievements': st.column_config.NumberColumn('Achievements', format='%d 🌟'),
                    'quiz_accuracy': st.column_config.NumberColumn('Quiz Accuracy', format='%.1f%%')
                }
            )
            
            # Show user's rank
            user_rank = next((i + 1 for i, x in enumerate(leaderboard) 
                            if x['username'] == st.session_state.current_user), 0)
            st.metric("Your Rank", f"#{user_rank}")
             # Top players visualization
            st.subheader("Top Players")
            top_players = leaderboard[:5]  # Get top 5 players
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[p['username'] for p in top_players],
                y=[p['points'] for p in top_players],
                text=[p['points'] for p in top_players],
                textposition='auto',
                name='Points'
            ))
            
            fig.update_layout(
                title='Top 5 Players',
                xaxis_title='Players',
                yaxis_title='Points',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

    with tabs[7]:  # This is the Beverages tab
      st.subheader("🍹 Your Beverage Collection")
      beverage_recipes = [recipe for recipe in user_data.get('created_recipes', []) 
                       if recipe.get('type') == 'beverage']
    
      # Add statistics at the top
      if beverage_recipes:
          col1, col2, col3 = st.columns(3)
          with col1:
            st.metric("Total Beverages Created", len(beverage_recipes))
          with col2:
            beverage_types = [recipe['name'].split()[0] for recipe in beverage_recipes]
            most_common = max(set(beverage_types), key=beverage_types.count)
            st.metric("Favorite Type", most_common)
          with col3:
            latest = max(beverage_recipes, key=lambda x: x['date'])
            st.metric("Last Created", latest['date'].split()[0])
        
         # Display beverage recipes
          for recipe in beverage_recipes:
            with st.expander(f"{recipe['date']} - {recipe['name']}"):
                st.write("**Ingredients used:**")
                st.write(", ".join(recipe['ingredients']))
                st.write("**Recipe details:**")
                st.write(recipe['details'])
        
        # Add visualization
          st.subheader("Beverage Types Distribution")
          type_counts = pd.DataFrame(beverage_types).value_counts().reset_index()
          type_counts.columns = ['Type', 'Count']
        
          fig = px.pie(
            type_counts,
            values='Count',
            names='Type',
            title='Your Beverage Types Distribution',
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD93D']
        )
          fig.update_traces(textposition='inside', textinfo='percent+label')
          st.plotly_chart(fig, use_container_width=True)
      else:
        st.info("No beverages created yet. Try the Beverage Generator!")

    with tabs[8]:  # This is the Desserts tab
      st.subheader("🍰 Your Dessert Collection")
      dessert_recipes = [recipe for recipe in user_data.get('created_recipes', []) 
                      if recipe.get('type') == 'dessert']
    
      if dessert_recipes:
        # Add statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Desserts Created", len(dessert_recipes))
        with col2:
            cuisines = [recipe.get('cuisine', 'Other') for recipe in dessert_recipes]
            most_common_cuisine = max(set(cuisines), key=cuisines.count)
            st.metric("Favorite Cuisine", most_common_cuisine)
        with col3:
            latest = max(dessert_recipes, key=lambda x: x['date'])
            st.metric("Last Created", latest['date'].split()[0])
        
        # Display dessert recipes
        for recipe in dessert_recipes:
            with st.expander(f"{recipe['date']} - {recipe['name']}"):
                st.write("**Cuisine Type:**", recipe.get('cuisine', 'Not specified'))
                st.write("**Ingredients used:**")
                st.write(", ".join(recipe['ingredients']))
                if recipe.get('dietary_restrictions'):
                    st.write("**Dietary Restrictions:**")
                    st.write(", ".join(recipe['dietary_restrictions']))
                st.write("**Recipe details:**")
                st.write(recipe['details'])
        
        # Add visualization
        st.subheader("Dessert Types Distribution")
        dessert_types = [recipe['name'].split()[1] for recipe in dessert_recipes]
        type_counts = pd.DataFrame(dessert_types).value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        
        fig = px.pie(
            type_counts,
            values='Count',
            names='Type',
            title='Your Dessert Types Distribution',
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD93D']
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
      else:
        st.info("No desserts created yet. Try the Dessert Generator!")
    

# Check login first
check_login_required()
    
# Show sidebar and get selected mode
app_mode = show_sidebar()
    
# Get current user's data
user_data = st.session_state.users[st.session_state.current_user]
if app_mode == "Profile":
   show_user_profile(user_data)    


# Main Content

if app_mode == "Dashboard":
    st.title("🍽️ PlatePals ")
    
    # Key Metrics
 
   # Menu Performance    
    st.subheader("📊 Menu Performance")
    menu_df = pd.DataFrame([
        {"Dish": "Truffle Risotto", "Rating": 4.4, "Category": "Main Course"},
        {"Dish": "Seared Salmon", "Rating": 4.7, "Category": "Seafood"},
        {"Dish": "Molten Chocolate Cake", "Rating": 4.9, "Category": "Dessert"},
        {"Dish": "Paneer ki Sabji", "Rating": 4.2, "Category": "Main Course"},
        {"Dish": "Mixed Berry and Seasonal Fruits Smoothie", "Rating": 4.1, "Category": "Beverage"},
    ])

    fig = px.bar(
        menu_df,
        x="Dish",
        y="Rating",
        color="Category",
        text="Rating",
        title="Top Performing Dishes",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(range=[0, 5]),
        plot_bgcolor="rgba(0,0,0,0)",
        title_font_size=20
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # QUICK INSIGHTS
    # -----------------------------
    st.markdown("### 🔍 Quick Insights")

    col4, col5 = st.columns(2)

    with col4:
        st.success("🥇 Highest Rated Dish: **Molten Chocolate Cake**")

    with col5:
        st.info("🔥 Most Popular Category: **Desserts**")


elif app_mode == "Search":
    st.title("🔍 Search")
    st.subheader("Search for any recipe and get detailed information")

    # Search interface
    search_query = st.text_input("Enter recipe name to search:", 
                                placeholder="e.g., Butter Chicken, Tiramisu, Pad Thai...")

    if st.button("Search Recipe", type="primary"):
        if search_query:
            with st.spinner("Searching for recipe details..."):
                # Create detailed prompt for recipe search
                prompt = f"""Search and provide detailed information for {search_query}. 
                Include all of these details:

                1. Recipe Overview:
                   - Traditional origin/cuisine
                   - Brief description
                   - Serving size
                   - Total calories per serving

                2. Time Requirements:
                   - Preparation time
                   - Cooking time
                   - Total time
                   - Difficulty level

                3. Ingredients:
                   - Detailed list with exact measurements
                   - Possible substitutes for hard-to-find ingredients
                   - Required kitchen equipment

                4. Nutritional Information:
                   - Calories
                   - Protein
                   - Carbohydrates
                   - Fats
                   - Fiber
                   - Key vitamins and minerals

                5. Step-by-Step Instructions:
                   - Detailed preparation steps
                   - Cooking steps
                   - Critical temperature points (if applicable)
                   - Visual cues for each step

                6. Tips and Variations:
                   - Chef's tips
                   - Common mistakes to avoid
                   - Recipe variations
                   - Storage instructions
                   - Reheating guidelines

                7. Serving Suggestions:
                   - Plating recommendations
                   - Garnishing ideas
                   - Recommended side dishes
                   - Beverage pairings

                8. Additional Notes:
                   - Seasonal considerations
                   - Dietary information
                   - Health benefits
                   - Cultural significance (if any)
                """

                recipe_info = generate_recipe_with_timeout(prompt)
                
                if recipe_info:
                    st.success("✨ Recipe found! Here are the details:")

                    with st.expander("📖 View Complete Recipe Details", expanded=True):
                        st.write(recipe_info)
                    
                    # Add YouTube link with more visible styling
                    st.markdown("---")
                    st.subheader("🎥 Watch Recipe Videos")
                    youtube_query = quote(f"{search_query} recipe cooking")
                    youtube_link = f"https://www.youtube.com/results?search_query={youtube_query}"
                    st.markdown(
                        f"""
                        <div style='text-align: center; padding: 10px; margin: 10px 0; background-color: #f0f2f6; border-radius: 5px;'>
                            <a href='{youtube_link}' target='_blank' style='color: red; text-decoration: none;'>
                                <span style='font-size: 20px;'>🎥 Watch {search_query} Recipe Videos on YouTube</span>
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown("---")


                    # Save search to user's history
                    user = st.session_state.users[st.session_state.current_user]
                    if 'recipe_searches' not in user:
                        user['recipe_searches'] = []
                    
                    # Save search with more details
                    user['recipe_searches'].append({
                        'recipe': search_query,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'details': recipe_info,
                        'youtube_link': f"https://www.youtube.com/results?search_query={quote(search_query + ' recipe')}",
                        'search_timestamp': datetime.now().timestamp()
                    })
                    
                    # Update user data
                    st.session_state.user_manager.update_user_data(
                        st.session_state.current_user, 
                        user
                    )
                    
                    # Award points
                    add_points(5, f"Searched recipe: {search_query}")
                    st.success("🎉 +5 points awarded for recipe search!")

                    # Show related recipes suggestion
                    st.subheader("📚 You might also like:")
                    related_prompt = f"Suggest 3 similar recipes to {search_query} with brief descriptions"
                    related_recipes = model.generate_content(related_prompt).text
                    st.write(related_recipes)

        else:
            st.warning("Please enter a recipe name to search")

    # Show recent searches
    st.subheader("📅 Recent Searches")
    user = st.session_state.users[st.session_state.current_user]
    if 'recipe_searches' in user and user['recipe_searches']:
        for search in reversed(user['recipe_searches'][-5:]):  # Show last 5 searches
            with st.expander(f"{search['date']} - {search['recipe']}"):
                st.write(search['details'])
    else:
        st.info("No recent searches yet")



elif app_mode == "Recipe Suggestions":
    st.title("Recipe Suggestions")

        # New user preferences section
    st.subheader("Your Preferences")
    col1, col2 = st.columns(2)
    
    with col1:
        user_mood = st.selectbox(
            "How are you feeling today?",
            options=["Very Sad 😢", "Sad 😔", "Neutral 😐", "Happy 😊", "Very Happy 😄", "Emotional", "Excited 😍", "Energetic 💪", "Relaxed 😌", "Tired", "Angry"]
        )
        
        hunger_level = st.selectbox(
            "How hungry are you?",
            options=["Just a Snack", "Slightly Hungry", "Moderately Hungry", "Very Hungry", "Starving"]
        )
    
    with col2:
        current_date = datetime.now()
        date = st.date_input("Date", current_date)
        time_of_day = st.selectbox(
            "Time of day",
            ["Breakfast", "Lunch", "Evening Snack", "Dinner", "Late Night"]
        )
        
        calorie_limit = st.number_input(
            "Desired calorie limit (kcal)",
            min_value=100,
            max_value=20000,
            value=500,
            step=50
        )

    # Dietary Preferences
    st.subheader("🥗 Dietary Preferences")
    dietary_prefs = st.multiselect(
        "Select your dietary preferences",
        ["Jain", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", 
         "High-Protein", "Low-Carb", "Mediterranean", "Paleo", "Pescatarian",
         "Nut-Free", "Sugar-Free", "Low-Sodium", "Halal", "Kosher"]
    )

    # Get and filter ingredients
    st.subheader("🥗 Ingredients Selection")
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search or add ingredients", 
                                  help="Type any ingredient - it will be added if not found")
    with col2:
        show_categories = st.checkbox("Show categories", value=False)
    
    # Get and filter ingredients 
    all_ingredients = get_all_ingredients()
    if search_term:
        filtered_ingredients = search_ingredients(search_term, all_ingredients)
    else:
        filtered_ingredients = all_ingredients
    
    if show_categories:
        category = st.selectbox("Filter by category", list(st.session_state.inventory.keys()))
        filtered_ingredients = [i for i in filtered_ingredients if i in st.session_state.inventory[category]]
    
    selected_ingredients = st.multiselect(
        "Selected Ingredients",
        options=sorted(filtered_ingredients),
        default=[search_term.title()] if search_term else [],
        key="recipe_ingredients"
    )

    mentions = get_user_mentions()

    if st.button("Generate Recipe", type="primary"):
        if selected_ingredients:
            with st.spinner("Creating your personalized recipe..."):
                # Enhanced prompt with user preferences
                prompt = f"""Create a detailed recipe considering these factors:
                User Preferences:
                - Current Mood: {user_mood}
                - Hunger Level: {hunger_level}
                - Time of Day: {time_of_day}
                - Calorie Limit: {calorie_limit} kcal
                
                Special Mentions:
                {f"Must Include: {mentions['wants']}" if mentions['wants'] else ""}
                {f"Must Avoid: {mentions['dont_wants']}" if mentions['dont_wants'] else ""}
                {f"Additional Notes: {mentions['additional_notes']}" if mentions['additional_notes'] else ""}


                Recipe Requirements:
                - Must use these ingredients: {', '.join(selected_ingredients)}
                - Total calories should not exceed {calorie_limit} kcal
                - Suitable for {time_of_day.lower()} time
                - Portion size based on hunger level: {hunger_level}
                
                Please include:
                - Recipe name
                - Total calories per serving
                - Preparation time
                - Cooking time
                - Detailed ingredients list with measurements
                - Step-by-step instructions
                - Nutritional information
                - Mood-boosting benefits (if any)
                - Tips for portion control
                """
                
                recipe = model.generate_content(prompt).text
                if recipe:
                    st.session_state.generated_recipe = recipe
                    st.success("Recipe generated successfully!")
                    
                    # Save enhanced recipe data to user's profile
                    user = st.session_state.users[st.session_state.current_user]
                    user['created_recipes'].append({
                        'name': f"Recipe with {', '.join(selected_ingredients)}",
                        'details': recipe,
                        'date': date.strftime("%Y-%m-%d"),
                        'time_of_day': time_of_day,
                        'user_mood': user_mood,
                        'hunger_level': hunger_level,
                        'calorie_limit': calorie_limit,
                        'ingredients': selected_ingredients,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    
                    add_points(5, "Generated personalized recipe")
                    check_achievements(user, "recipe")
        else:
            st.warning("Please select ingredients first")
            
    if st.session_state.generated_recipe:
        with st.expander("📖 View Full Recipe", expanded=True):
            st.text_area(
                "Complete Recipe",
                st.session_state.generated_recipe,
                height=600
            )

elif app_mode == "Leftover Management":
    st.title("â™»ï¸ Leftover Management")
    
    # Input section with enhanced details
    st.subheader("Add Leftover Ingredient")
    col1, col2 = st.columns(2)
    
    with col1:
        ingredient_name = st.text_input("Ingredient Name")
        ingredient_type = st.selectbox(
            "Ingredient Type",
            ["Vegetable", "Fruit", "Grain", "Protein", "Dairy", "Herb/Spice", 
             "Condiment", "Sauce", "Baked Good", "Beverage", "Snack", "Other"]
        )
        cuisine_origin = st.selectbox(
            "Cuisine Origin",
            ["International", "Indian", "Italian", "Chinese", "Mexican", 
             "Japanese", "Thai", "Mediterranean", "American", "Other"]
        )

        # Expiry date input
        expiry_date = st.date_input(
            "Best Before Date",
            min_value=datetime.now().date()
        )
    
    with col2:
        quantity = st.number_input("Quantity (in grams)", min_value=1, value=100, step=10)
        storage_condition = st.selectbox(
            "Storage Condition",
            ["Refrigerated", "Frozen", "Room Temperature", "Pantry", 
             "Air-Tight Container", "Vacuum Sealed", "Zip-Lock Bag"]
        )
        freshness = st.select_slider(
            "Freshness Level",
            options=["Need to use immediately", "Good for 1-2 days", "Fresh", "Very Fresh"]
        )
    
    if st.button("Add Ingredient", type="primary"):
        if ingredient_name:
            user = st.session_state.users[st.session_state.current_user]
            user['leftover_ingredients'].append({
                'name': ingredient_name,
                'type': ingredient_type,
                'quantity': quantity,
                'storage': storage_condition,
                'freshness': freshness,
                'expiry_date': expiry_date.strftime("%Y-%m-%d"),
                'date_added': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success(f"Added {quantity}g of {ingredient_name}")
            add_points(2, f"Added leftover: {ingredient_name}")
            check_achievements(user, "leftover")
            st.rerun()
    
    # Display current leftovers with filtering
    st.subheader("Current Leftovers")
    user = st.session_state.users[st.session_state.current_user]
    
    if user['leftover_ingredients']:
        # Filtering options
        col1, col2 = st.columns(2)
        with col1:
            type_filter = st.multiselect(
                "Filter by Type",
                options=["Vegetable", "Fruit", "Grain", "Protein", "Dairy", "Herb/Spice", "Other"]
            )
        with col2:
            storage_filter = st.multiselect(
                "Filter by Storage",
                options=["Refrigerated", "Frozen", "Room Temperature", "Pantry"]
            )
        
        # Filter the leftovers
        leftovers_df = pd.DataFrame(user['leftover_ingredients'])
        if type_filter:
            leftovers_df = leftovers_df[leftovers_df['type'].isin(type_filter)]
        if storage_filter:
            leftovers_df = leftovers_df[leftovers_df['storage'].isin(storage_filter)]
        
        st.dataframe(
            leftovers_df[['name', 'type', 'quantity', 'storage', 'freshness', 'expiry_date', 'date_added']], 
            hide_index=True
        )
        
        # Enhanced Recipe Generation
        st.subheader("Generate Recipe from Leftovers")
        
        # Recipe preferences
        col1, col2 = st.columns(2)
        with col1:
            cooking_time = st.slider(
                "Maximum Cooking Time (minutes)",
                min_value=10,
                max_value=120,
                value=30,
                step=5
            )
            calorie_target = st.number_input(
                "Target Calories per Serving",
                min_value=100,
                max_value=20000,
                value=400,
                step=50
            )
        
        with col2:
            meal_type = st.selectbox(
                "Meal Type",
                ["Quick Snack", "Breakfast", "Lunch", "Dinner", "Side Dish", "Appetizer", "Other"]
            )
            difficulty_level = st.select_slider(
                "Cooking Skill Level",
                options=["Very Easy", "Easy", "Moderate", "Advanced", "Expert"]
        )
        
        # Ingredient selection
        selected = st.multiselect(
            "Select ingredients for recipe",
            options=[item['name'] for item in user['leftover_ingredients']]
        )
        
        dietary_prefs = st.multiselect(
            "Dietary Preferences",
            ["Jain", "Vegetarian", "Vegan", "Gluten-Free", "Low-Carb", "High-Protein"]
        )
        
        mentions = get_user_mentions()

    if st.button("Generate Recipe", type="primary") and selected:
        # First create the ingredients list
        ingredients_with_details = []
        for ingredient in selected:
            item = next(item for item in user['leftover_ingredients'] 
                       if item['name'] == ingredient)
            ingredients_with_details.append({
                'name': ingredient,
                'quantity': item['quantity'],
                'type': item['type']
            })
    
        # Then create the prompt
        prompt = f"""Create a detailed recipe with these specifications:
        Ingredients: {', '.join(f"{i['name']} ({i['quantity']}g)" for i in ingredients_with_details)}
        
        Requirements:
        - Meal Type: {meal_type}
        - Maximum Cooking Time: {cooking_time} minutes
        - Target Calories: {calorie_target} calories per serving
        - Difficulty Level: {difficulty_level}
        {f"- Dietary Restrictions: {', '.join(dietary_prefs)}" if dietary_prefs else ""}
        
        Special Requirements:
        {f"Must Include: {mentions['wants']}" if mentions['wants'] else ""}
        {f"Must Avoid: {mentions['dont_wants']}" if mentions['dont_wants'] else ""}
        {f"Additional Notes: {mentions['additional_notes']}" if mentions['additional_notes'] else ""}


        Please include:
        1. Recipe name
        2. Preparation time and Cooking time
        3. Exact measurements and instructions
        4. Nutritional information (especially calories)
        5. Cooking tips and variations
        6. Storage suggestions for leftovers
        """
        
        import time

        COOLDOWN_SECONDS = 30
        current_time = time.time()

        if current_time - st.session_state.last_gemini_call < COOLDOWN_SECONDS:
            wait_time = int(COOLDOWN_SECONDS - (current_time - st.session_state.last_gemini_call))
            st.warning(f"â³ Please wait {wait_time} seconds before generating another recipe.")
        else:
            recipe = generate_recipe_with_timeout(prompt)
            st.session_state.last_gemini_call = current_time

        if recipe:
            with st.expander("📖 View Generated Recipe", expanded=True):
                st.success("âœ¨ Recipe generated successfully!")
                st.write(recipe)
                
                # Save the recipe with enhanced details
                user['leftovers'].append({
                    'name': f"Leftover Recipe ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                    'ingredients': ingredients_with_details,
                    'meal_type': meal_type,
                    'cooking_time': cooking_time,
                    'calories': calorie_target,
                    'difficulty': difficulty_level,
                    'dietary_prefs': dietary_prefs,
                    'recipe': recipe,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                add_points(5, "Generated leftover recipe")
            # Option to remove used ingredients
            if st.button("âœ… Mark Ingredients as Used"):
                user['leftover_ingredients'] = [
                    item for item in user['leftover_ingredients']
                    if item['name'] not in selected
                ]
                st.success("Ingredients marked as used")
                st.rerun()
    else:
        st.info("No leftovers added yet")

elif app_mode == "Menu Personalization":
    st.title("🍽️ Complete Meal Planner")
    
    # General Preferences
    st.subheader("🎯 Meal Preferences")
    col1, col2 = st.columns(2)
    
    with col1:
        cuisine_type = st.selectbox(
            "Cuisine Type",
            ["International", "Indian", "Italian", "Chinese", "Mexican", 
             "Japanese", "Thai", "Mediterranean", "American", "French"]
        )
        
        meal_occasion = st.selectbox(
            "Meal Occasion",
            ["Regular Meal", "Special Dinner", "Party", "Date Night", 
             "Family Gathering", "Business Lunch", "Festive Celebration"]
        )
    
    with col2:
        spice_level = st.select_slider(
            "Spice Level",
            options=["Mild", "Medium", "Spicy", "Very Spicy"]
        )
        
        serving_size = st.number_input(
            "Number of Servings",
            min_value=1,
            max_value=20,
            value=2
        )

    # Dietary Restrictions
    st.subheader("🥗 Dietary Preferences")
    dietary_prefs = st.multiselect(
        "Select any dietary restrictions",
        ["Jain", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", 
         "Nut-Free", "Low-Carb", "Keto", "Halal", "Kosher"]
    )

    # Course-specific Preferences
    st.subheader("🍽️ Course Preferences")
    
    # Appetizer Preferences
    with st.expander("Appetizer/Starter", expanded=True):
        app_type = st.selectbox(
            "Appetizer Type",
            ["Hot", "Cold", "Soup", "Salad", "Finger Food", "Dips","Nachos",
             "Bruschetta", "Spring Rolls", "Stuffed Vegetables", "Other"]
        )
        app_prep_time = st.slider(
            "Maximum Preparation Time (minutes)",
            min_value=5,
            max_value=60,
            value=15,
            step=5,
            key="app_time"
        )

    # Main Course Preferences
    with st.expander("Main Course", expanded=True):
        main_protein = st.selectbox(
            "Primary Protein",
            ["Vegies", "Chicken", "Fish", "Lamb", "Beef", "Tofu", "Paneer", 
             "Legumes", "None (Vegetarian)", "Jain"]
        )
        main_style = st.selectbox(
            "Cooking Style",
            ["Grilled", "Baked", "Stir-fried", "Curry", "Roasted", 
             "Steamed", "Pan-seared","Slow-cooked","other"]
        )

    # Beverage Preferences
    with st.expander("Beverage", expanded=True):
        bev_type = st.selectbox(
            "Beverage Type",
            ["Mocktail", "Fresh Juice", "Smoothie", "Hot Beverage", 
             "Iced Tea", "Lemonade", "Traditional Drink"]
        )
        bev_style = st.selectbox(
            "Beverage Style",
            ["Sweet", "Tangy", "Refreshing", "Creamy", "Spiced", "Fruity"]
        )

    # Dessert Preferences
    with st.expander("Dessert", expanded=True):
        dessert_type = st.selectbox(
            "Dessert Type",
            ["Cake", "Pudding", "Ice Cream", "Traditional Sweet", 
             "Pie", "Mousse", "Fresh Fruit Based"]
        )
        dessert_pref = st.multiselect(
            "Dessert Preferences",
            ["Low Sugar", "Fresh Fruit", "Chocolate", "Cold", "Hot", 
             "Quick & Easy"]
        )

    mentions = get_user_mentions()

    if st.button("Generate Complete Menu", type="primary"):
        with st.spinner("Creating your personalized menu..."):
            # Create comprehensive prompt for all courses
            prompt = f"""Create a complete {cuisine_type} menu for {meal_occasion} with {serving_size} servings.

            Dietary Restrictions: {', '.join(dietary_prefs) if dietary_prefs else 'None'}
            Spice Level: {spice_level}

            Special Requirements:
            {f"Must Include: {mentions['wants']}" if mentions['wants'] else ""}
            {f"Must Avoid: {mentions['dont_wants']}" if mentions['dont_wants'] else ""}
            {f"Additional Notes: {mentions['additional_notes']}" if mentions['additional_notes'] else ""}

            Please provide:

            1. APPETIZER:
            - Type: {app_type}
            - Preparation Time: {app_prep_time} minutes maximum
            - Include recipe and presentation suggestions

            2. MAIN COURSE:
            - Primary Protein: {main_protein}
            - Cooking Style: {main_style}
            - Include sides and accompaniments
            - Include recipe and plating suggestions

            3. BEVERAGE:
            - Type: {bev_type}
            - Style: {bev_style}
            - Include recipe and serving suggestions
            - Include garnishing ideas

            4. DESSERT:
            - Type: {dessert_type}
            - Preferences: {', '.join(dessert_pref) if dessert_pref else 'Standard'}
            - Include recipe and presentation tips

            For each course, provide:
            - Dish name
            - Ingredients list with quantities
            - Step-by-step preparation instructions
            - Preparation time
            - Cooking/assembly time
            - Presentation suggestions
            - Any special tips or variations
            """

            menu = generate_recipe_with_timeout(prompt)
            if menu:
                st.success("âœ¨ Complete menu generated successfully!")
                
                # Display the menu in an organized way
                with st.expander("📋 View Complete Menu", expanded=True):
                    st.write(menu)
                    
                    # Save to user's profile
                    user = st.session_state.users[st.session_state.current_user]
                    user['created_recipes'].append({
                        'name': f"{cuisine_type} {meal_occasion} Menu",
                        'type': 'complete_menu',
                        'cuisine': cuisine_type,
                        'occasion': meal_occasion,
                        'servings': serving_size,
                        'details': menu,
                        'dietary_restrictions': dietary_prefs,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    
                    # Add points and check achievements
                    add_points(15, "Generated complete menu")
                    check_achievements(user, "recipe")

elif app_mode == "Event Manager":
    st.title("🎉 Event Manager")
    
    # Create tabs for different event management functions
    tab1, tab2, tab3 = st.tabs(["Create Event", "View Events", "Event Analytics"])
    
    with tab1:
        st.subheader("Plan New Event")
        
        col1, col2 = st.columns(2)
        with col1:
            event_name = st.text_input("Event Name")
            event_date = st.date_input("Event Date")
            guest_count = st.number_input("Number of Guests", min_value=2, value=20)
        
        with col2:
            event_theme = st.selectbox("Event Theme", 
                ["Mediterranean", "Asian Fusion", "Traditional", "Modern American", 
                 "Indian", "Mexican", "Italian", "Casual Buffet"])
            
            dietary_restrictions = st.multiselect(
                "Dietary Restrictions",
                ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", 
                 "Nut-Free", "Halal", "Kosher"]
            )
        
        # Menu Planning
        st.subheader("Menu Planning")
        courses = ["Appetizers", "Main Course", "Desserts", "Beverages"]
        menu_items = {}
        
        for course in courses:
            st.write(f"**{course}**")
            col1, col2 = st.columns(2)
            
            with col1:
                # Get suggestions based on theme and restrictions
                if st.button(f"Get {course} Suggestions"):
                    with st.spinner("Generating suggestions..."):
                        prompt = f"""Suggest 3 {course.lower()} for a {event_theme} themed event with {guest_count} guests.
                        Must accommodate these dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
                        Include brief descriptions."""
                        
                        suggestions = get_recipe_from_gemini([], dietary_restrictions)
                        if suggestions:
                            st.write(suggestions)
                            add_points(2, f"Generated {course.lower()} suggestions")
            
            with col2:
                menu_items[course] = st.text_area(f"Selected {course}", height=100,
                    placeholder=f"Enter selected {course.lower()} here...")
        
        # Cost Estimation
        st.subheader("Cost Estimation")
        per_person_cost = st.number_input("Estimated Cost per Person (â‚¹)", min_value=200.0, value=250.0)
        total_cost = per_person_cost * guest_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Estimated Cost", f"â‚¹{total_cost:,.2f}")
        with col2:
            st.metric("Cost per Person", f"â‚¹{per_person_cost:.2f}")
        with col3:
            st.metric("Total Guests", guest_count)
        
        # Save Event
        if st.button("Save Event"):
            if event_name and event_date:
                new_event = {
                    "name": event_name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "guests": guest_count,
                    "theme": event_theme,
                    "dietary_restrictions": dietary_restrictions,
                    "menu": menu_items,
                    "cost_per_person": per_person_cost,
                    "total_cost": total_cost,
                    "status": "Upcoming"
                }
                # Save to both global and user-specific events
                st.session_state.events.append(new_event)
                user = st.session_state.users[st.session_state.current_user]
                user['completed_events'].append(new_event)
                add_points(10, f"Created new event: {event_name}")
                st.success("Event saved successfully!")
                add_points(5, f"Created new event: {event_name}")
            else:
                st.error("Please fill in event name and date")
    
    with tab2:
        st.subheader("Upcoming Events")
        
        if not st.session_state.events:
            st.info("No events planned yet")
        else:
            for idx, event in enumerate(st.session_state.events):
                with st.expander(f"{event['date']} - {event['name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Theme:** {event['theme']}")
                        st.write(f"**Guests:** {event['guests']}")
                        st.write(f"**Status:** {event['status']}")
                    
                    with col2:
                        st.write("**Dietary Restrictions:**")
                        for restriction in event['dietary_restrictions']:
                            st.write(f"- {restriction}")
                    
                    if 'menu' in event:
                        st.write("**Menu:**")
                        for course, items in event['menu'].items():
                            if items.strip():  # Only show if items were added
                                st.write(f"*{course}:*")
                                st.write(items)
                    
                    # Event actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Mark Complete {idx}"):
                            st.session_state.events[idx]['status'] = "Completed"
                            st.rerun()
                    with col2:
                        if st.button(f"Delete Event {idx}"):
                            st.session_state.events.pop(idx)
                            st.rerun()
    
    with tab3:
        st.subheader("Event Analytics")
        
        if not st.session_state.events:
            st.info("No events data available")
        else:
            # Convert events to DataFrame for analysis
            events_df = pd.DataFrame(st.session_state.events)
            
            # Event count by theme
            fig_themes = px.pie(events_df, names='theme', title='Events by Theme')
            st.plotly_chart(fig_themes, use_container_width=True)
            
            # Guest distribution
            fig_guests = px.box(events_df, y='guests', title='Guest Count Distribution')
            st.plotly_chart(fig_guests, use_container_width=True)
            
            # Cost analysis
            if 'total_cost' in events_df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Revenue", f"${events_df['total_cost'].sum():,.2f}")
                with col2:
                    st.metric("Average Event Cost", 
                             f"â‚¹{events_df['total_cost'].mean():,.2f}")

elif app_mode == "Cooking Quiz":
    st.title("👩‍🍳 Cooking Knowledge Quiz")
    st.write("Test your cooking knowledge and earn points!")
    
    # Get current user's quiz stats
    user = st.session_state.users[st.session_state.current_user]
    quiz_stats = user['quiz_stats']
    
    # Display quiz statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Attempts", quiz_stats['total_attempts'])
    with col2:
        accuracy = 0 if quiz_stats['total_attempts'] == 0 else \
                  (quiz_stats['correct_answers'] / quiz_stats['total_attempts']) * 100
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    # Quiz Interface
    if 'current_question' not in st.session_state:
        st.session_state.current_question = random.choice(COOKING_QUIZ)
    
    st.subheader("Question:")
    question = st.session_state.current_question
    st.write(question["question"])
    
    user_answer = st.radio("Select your answer:", question["options"], key="quiz_answer")
    
    if st.button("Submit Answer"):
        quiz_stats = user['quiz_stats']
        quiz_stats['total_attempts'] += 1
        
        if user_answer == question["correct"]:
            st.success("🎉 Correct! +5 points")
            add_points(5, "Correct quiz answer")
            quiz_stats['correct_answers'] += 1
            # Update streak
            user['current_streak'] = user.get('current_streak', 0) + 1
        else:
            st.error(f"âŒ Wrong answer. -10 points. Correct answer was: {question['correct']}")
            add_points(-10, "Wrong quiz answer")
            # Reset streak on wrong answer
            user['current_streak'] = 0
        
        # Check for achievements
        check_achievements(user, "quiz")
        
        # Get new question
        new_questions = [q for q in COOKING_QUIZ if q != question]
        if new_questions:
            st.session_state.current_question = random.choice(new_questions)
        
        # Show quiz statistics
        st.write(f"Current streak: {user.get('current_streak', 0)} correct answers")
        
        # Show continue button
        if st.button("Next Question"):
            st.rerun()


elif app_mode == "Beverage Generator":
    st.title("🍹 Beverage Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        beverage_type = st.selectbox(
            "Beverage Type",
            ["Mocktail", "Hot Beverage", "Smoothie", "Fresh Juice", "Milkshake", "Cocktail", "Soda", "Shake", "Slush", "Frappe", "Iced Tea", "Iced Coffee","Alcoholic Beverage"]
        )
        
        # Add ingredient search functionality
        ingredient_search = st.text_input("🔍 Search or add ingredients", 
            help="Type any ingredient - it will be added if not found")
        
        # Get and filter ingredients
        all_ingredients = get_all_ingredients() + [
            "Mint", "Lemon", "Lime", "Orange", "Apple", "Mango", "Strawberry",
            "Honey", "Sugar Syrup", "Ginger", "Cinnamon", "Ice", "Chocolate Syrup",
            "Vanilla Extract", "Coconut Milk", "Almond Milk", "Soda Water", "Tonic Water",
            "Grenadine", "Pineapple Juice", "Cranberry Juice", "Peach Nectar",
            "Pomegranate Juice", "Kiwi", "Papaya", "Passion Fruit", "Blueberry",
            "Raspberry", "Blackberry", "Watermelon", "Cucumber", "Carrot", "Celery",
            "Beetroot", "Spinach", "Kale", "Avocado", "Peanut Butter", "Chocolate" ,
            "Coffee Beans", "Tea Leaves", "Herbal Tea", "Chai Spices", "Matcha",
            "Lavender", "Rose Water", "Cardamom", "Nutella", "Vanilla Bean", "Cocoa Powder",
            "Whipped Cream", "Maraschino Cherry", "Sprinkles", "Chocolate Chips",
            "Gummy Bears", "Fruit Garnish", "Mint Leaves", "Basil", "Thyme",
            "Rosemary", "Sage", "Parsley", "Chili Powder", "Cayenne Pepper"
        ]
        
        if ingredient_search:
            filtered_ingredients = search_ingredients(ingredient_search, all_ingredients)
        else:
            filtered_ingredients = all_ingredients
        
        selected_ingredients = st.multiselect(
            "Selected Ingredients",
            options=sorted(filtered_ingredients),
            default=[ingredient_search.title()] if ingredient_search else [],
            key="beverage_ingredients"
        )
        
        base_ingredients = st.multiselect(
            "Base Liquids",
            ["Milk", "Yogurt", "Coffee", "Tea", "Fruit Juice", "Coconut Water", "Sparkling Water", "Soda", "Alcohol", "Non-Alcoholic Spirits", "Herbal Infusion", "Nut Milk", "Fruit Puree", "Vegetable Juice"]
        )

    with col2:
        preferences = st.multiselect(
            "Flavor Preferences",
            ["Sweet", "Refreshing", "Citrus", "Creamy", "Spicy", "Herbal", "Frozen", "Fruity", "Savory", "Nutty", "Chocolatey", "Bitter", "Sour", "Smoky", "Earthy", "Floral", "Tangy", "Umami", "Salty", "Savory", "Spicy"]
        )
        
        seasonal = st.selectbox("Seasonal Preference", 
            ["All Seasons", "Summer", "Winter", "Spring", "Fall", "Rainy"])
        
        dietary_restrictions = st.multiselect(
            "Dietary Restrictions",
            ["Dairy-Free", "Sugar-Free", "Vegan", "Low-Calorie", "Gluten-Free", "Nut-Free", "Low-Carb", "High-Protein", "Paleo", "Keto"]
        )

    mentions = get_user_mentions()

    if st.button("Generate Beverage Recipe", type="primary"):
        if beverage_type and (selected_ingredients or base_ingredients):
            with st.spinner("Creating your beverage recipe..."):
                all_ingredients = selected_ingredients + base_ingredients
                prompt = f"""Create a detailed {beverage_type} recipe with the following details:
                - Beverage name
                - Description
                - Preparation time
                - Difficulty level
                - Main ingredients: {', '.join(all_ingredients)}
                - Preferences: {', '.join(preferences) if preferences else 'Any'}
                - Season: {seasonal}
                - Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}

                Special Requirements:
                {f"Must Include: {mentions['wants']}" if mentions['wants'] else ""}
                {f"Must Avoid: {mentions['dont_wants']}" if mentions['dont_wants'] else ""}
                {f"Additional Notes: {mentions['additional_notes']}" if mentions['additional_notes'] else ""}

                
                Include:
                - List of all ingredients with measurements
                - Step by step preparation instructions
                - Serving suggestions
                - Garnishing ideas
                - Tips for best results
                """
                
                recipe = model.generate_content(prompt).text
                if recipe:
                    st.success("Recipe generated successfully!")
                    st.write(recipe)
                    
                    # Save to user's data
                    user = st.session_state.users[st.session_state.current_user]
                    current_user = st.session_state.current_user
                    user['created_recipes'].append({
                    'name': f"{beverage_type} Recipe",
                    'type': 'beverage',
                    'ingredients': all_ingredients,
                    'details': recipe,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'dietary_restrictions': dietary_restrictions,  # Add this
                    'season': seasonal  # Add this
               })
                add_points(5, "Generated beverage recipe")
            # Add this line:
            current_user = st.session_state.current_user
            user = st.session_state.users[current_user]
            check_achievements(user, "beverage")
        else:
            st.warning("Please select a beverage type and at least one ingredient")


elif app_mode == "Dessert Generator":
    st.title("🍰 Dessert Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        dessert_type = st.selectbox(
            "Dessert Type",
            ["Cake", "Pie", "Cookie", "Ice Cream", "Pudding", "Pastry", 
             "Chocolate", "Custard", "Brownie", "Mousse", "Traditional Sweet",
             "Frozen Dessert", "Baked Dessert", "No-Bake Dessert"]
        )
        
        # Ingredient search
        ingredient_search = st.text_input("🔍 Search or add ingredients",
            help="Type any ingredient - it will be added if not found")
        
        # Base ingredients for desserts
        all_ingredients = get_all_ingredients() + [
            "Sugar", "Flour", "Butter", "Eggs", "Milk", "Cream", "Chocolate",
            "Vanilla Extract", "Baking Powder", "Cocoa Powder", "Nuts",
            "Fresh Fruits", "Honey", "Yogurt", "Cream Cheese", "Dark Chocolate",
            "White Chocolate", "Condensed Milk", "Whipping Cream", "Maple Syrup",
            "Cinnamon", "Nutmeg", "Caramel", "Berries", "Lemon Zest",
            "Orange Zest", "Almond Flour", "Coconut", "Peanut Butter"
        ]
        
        if ingredient_search:
            filtered_ingredients = search_ingredients(ingredient_search, all_ingredients)
        else:
            filtered_ingredients = all_ingredients
        
        selected_ingredients = st.multiselect(
            "Selected Ingredients",
            options=sorted(filtered_ingredients),
            default=[ingredient_search.title()] if ingredient_search else [],
            key="dessert_ingredients"
        )

    with col2:
        cuisine_type = st.selectbox(
            "Cuisine Type",
            ["International", "French", "Italian", "American", "Indian", 
             "Japanese", "Mexican", "Middle Eastern", "Mediterranean"]
        )
        
        dietary_restrictions = st.multiselect(
            "Dietary Restrictions",
            ["Gluten-Free", "Sugar-Free", "Vegan", "Dairy-Free", 
             "Nut-Free", "Egg-Free", "Low-Calorie", "Keto", "Paleo"]
        )
        
        preferences = st.multiselect(
            "Special Preferences",
            ["Quick & Easy", "Kid-Friendly", "Party Dessert", "Healthy Option",
             "Traditional", "Fusion", "Modern", "Low-Sugar", "Rich & Decadent"]
        )

    mentions = get_user_mentions()

    if st.button("Generate Dessert Recipe", type="primary"):
        if dessert_type and selected_ingredients:
            with st.spinner("Creating your dessert recipe..."):
                prompt = f"""Create a detailed {dessert_type} recipe from {cuisine_type} cuisine with these details:
                - Dessert name
                - Description
                - Preparation & cooking time
                - Difficulty level
                - Ingredients: {', '.join(selected_ingredients)}
                - Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
                - Preferences: {', '.join(preferences) if preferences else 'Standard'}

                Special Requirements:
                {f"Must Include: {mentions['wants']}" if mentions['wants'] else ""}
                {f"Must Avoid: {mentions['dont_wants']}" if mentions['dont_wants'] else ""}
                {f"Additional Notes: {mentions['additional_notes']}" if mentions['additional_notes'] else ""}


                Include:
                - Complete ingredients list with measurements
                - Step by step preparation instructions
                - Baking/cooking temperature and time (if applicable)
                - Serving suggestions
                - Decoration/plating tips
                - Storage instructions
                """
                
                recipe = model.generate_content(prompt).text
                if recipe:
                    st.success("Recipe generated successfully!")
                    st.write(recipe)
                    
                    # Save to user's data
                    user = st.session_state.users[st.session_state.current_user]
                    user['created_recipes'].append({
                        'name': f"{cuisine_type} {dessert_type}",
                        'type': 'dessert',
                        'cuisine': cuisine_type,
                        'ingredients': selected_ingredients,
                        'details': recipe,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'dietary_restrictions': dietary_restrictions
                    })
                    add_points(5, "Generated dessert recipe")
                    check_achievements(user, "dessert")
        else:
            st.warning("Please select a dessert type and at least one ingredient")

