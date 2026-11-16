# 🍽️ PlatePals — Serve Smart. Waste Less. Know More.
Made by Pravar Golecha

Link to use the app: https://plate-pals-by-pravar-golecha.streamlit.app/

## Brief Overview

I built **PlatePals**, an AI-powered smart restaurant and kitchen management web application developed using Streamlit, Python, and the Google Gemini API (`gemini-2.5-flash`). The platform brings together intelligent recipe generation, leftover inventory tracking, full-course meal planning, event catering management, and gamified culinary learning into a single interactive dashboard.

---

## Problem Statement and Brief About It

Commercial kitchens, catering services, and home cooks constantly struggle with three interconnected challenges:

1. **Food Wastage & Poor Inventory Utilization:** Perishable ingredients often expire because kitchen staff or home cooks lack quick ideas on how to combine available leftovers into viable dishes before their "best before" dates.
2. **Time-Consuming Menu & Event Planning:** Designing custom multi-course menus or estimating catering costs for events with varied dietary restrictions (e.g., Jain, Vegan, Gluten-Free, Keto) requires significant manual effort and culinary expertise.
3. **Lack of Engagement & Culinary Upskilling:** Traditional kitchen management tools are purely transactional and offer no interactive way for staff or users to test their food safety and culinary knowledge.

---

## Solution

To solve these problems, I designed **PlatePals** as an all-in-one culinary assistant powered by Generative AI. Instead of relying on static recipe databases, the application dynamically generates tailored recipes, multi-course menus, beverages, and desserts based on real-time user inputs—such as available leftovers, mood, hunger levels, calorie limits, and strict dietary constraints. To keep users engaged, I integrated a point-based gamification system, achievement badges, a social leaderboard, and an interactive cooking quiz.

---

## More About the Solution and Its Features

### Key Features

* **🤖 Context-Aware Recipe Suggestions:** Generates personalized recipes factoring in the user's current mood, hunger level, time of day, calorie limit, dietary preferences, and custom "Special Mentions" (what to strictly include or avoid).
* **♻️ Smart Leftover Management:** Allows users to log leftover ingredients with weight (in grams), storage conditions, freshness levels, and expiration dates. It then generates zero-waste recipes specifically utilizing those expiring items and lets users mark ingredients as used.
* **🔍 Deep-Dive Recipe Search:** Fetches comprehensive culinary breakdowns—including macro/micronutrients, kitchen equipment needed, step-by-step visual cues, plating tips, and direct YouTube video search links.
* **📋 Complete Meal Planner & Event Manager:**
* *Menu Personalization:* Builds cohesive 4-course meals (Appetizer, Main Course, Beverage, Dessert) tailored to specific occasions and spice levels.
* *Event Manager:* Helps plan catering events by generating theme-based course ideas, calculating per-person and total costs, and visualizing event analytics (guest distribution and theme breakdowns) via Plotly charts.


* **🍹 Dedicated Beverage & 🍰 Dessert Generators:** Specialized AI generators supporting seasonal preferences, base liquids, global cuisines, and dietary filters (e.g., Sugar-Free, Egg-Free).
* **🏆 Gamification, Quizzes & Social Leaderboard:** Users earn points for generating recipes, logging leftovers, and answering cooking/food-safety trivia. Includes streak tracking, unlockable achievement badges, friend connections, and a live leaderboard.

### Advantages & Innovativeness

* **Hyper-Personalization Beyond Ingredients:** Unlike standard recipe apps that only filter by ingredients, PlatePals adapts portion sizes and dish styles to psychological and situational cues like mood and hunger level.
* **Active Waste Reduction Loop:** By combining expiry tracking with AI recipe synthesis, it turns potential kitchen waste into actionable meal plans.
* **Behavioral Reinforcement:** Combining sustainability actions (managing leftovers) with points and achievements incentivizes consistent waste-reduction habits.

---

## Future Scope 

### 1. Future Scope

* **Real-Time Inventory Sync:** Automatically deduct ingredients from the main `st.session_state.inventory` and `leftover_ingredients` when a user marks a generated recipe as cooked.
* **OCR / Receipt & Fridge Scanning:** Use Gemini's multimodal vision capabilities so users can snap a photo of their fridge or grocery receipt to auto-populate inventory and expiry dates.
* **True Asynchronous API Calls:** Replace the blocking `time.sleep` progress bar with real async streaming (`asyncio` is already imported in the file) for faster, responsive recipe generation.
* **Restaurant POS & Cost Integration:** Expand the Event Manager's cost estimator into a full ingredient-level food cost calculator for commercial kitchens.

---

## Problems Faced During the Project

* **API Rate Limits & Quota Exhaustion (`429 ResourceExhausted`):** Frequent testing and rapid button clicks during recipe generation triggered Gemini API rate limits. I had to implement explicit exception handling for `429` errors and introduce a 30-second cooldown timer (`COOLDOWN_SECONDS = 30`) in the Leftover Management module.
* **Managing Complex Multi-Page State in Streamlit:** Because Streamlit reruns the entire script on every widget interaction, preserving user authentication, active quiz questions, generated recipes, and multi-tab profile analytics required careful structuring of `st.session_state` and an external `UserDataManager` class.
* **Enforcing Structured & Safe AI Outputs:** Getting the LLM to consistently respect strict dietary rules (like Jain or Allergen-free constraints) alongside custom user "wants" and "don't wants" required iterative prompt engineering and configuring Gemini safety thresholds (`BLOCK_MEDIUM_AND_ABOVE`).
* **Secrets & Environment Configuration:** Handling API keys across local development and deployment environments required building fallback logic to read from both `.streamlit/secrets.toml` and non-hidden `streamlit/secrets.toml` paths using `tomllib`/`toml`.


