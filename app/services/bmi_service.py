"""BMI calculation service with fun messages and health suggestions."""

import random


def calculate_bmi(height_cm: float, weight_kg: float) -> dict:
    """Calculate BMI and return result with category, message and suggestions."""
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category = "underweight"
        color = "#3b82f6"  # blue
        messages = [
            "You're a bit light! Time to add some healthy calories 🍎",
            "Looks like you could use some extra nutrients! Let's fix that 🥗",
            "A little underweight - your body deserves more fuel! 🔥",
            "You're lighter than ideal - let's bulk up healthily! 💪",
        ]
        suggestions = [
            "Eat more frequent, nutrient-dense meals",
            "Include healthy fats like nuts, avocado, and olive oil",
            "Add protein-rich foods to every meal",
            "Consider smoothies with fruits, yogurt, and nut butters",
            "Strength training can help build healthy muscle mass",
            "Consult a dietitian if you struggle to gain weight",
        ]
    elif bmi < 25:
        category = "normal"
        color = "#22c55e"  # green
        messages = [
            "You're healthy! Keep up the great work 😄",
            "Perfect balance! Your body thanks you 🌟",
            "Looking good! You're in the ideal range ✨",
            "Nailed it! Your BMI is spot-on 🎯",
            "Healthy and happy! Keep doing what you're doing 💚",
        ]
        suggestions = [
            "Maintain your balanced diet and regular exercise",
            "Stay hydrated with plenty of water",
            "Keep getting 7-9 hours of quality sleep",
            "Continue with regular health check-ups",
            "Mix up your workouts to stay motivated",
        ]
    elif bmi < 30:
        category = "overweight"
        color = "#f59e0b"  # orange
        messages = [
            "Time to exercise! Let's get moving 💪",
            "A few extra pounds - nothing we can't handle! 🏃",
            "Your body is asking for more activity! Let's go! 🚴",
            "Slightly overweight - small changes, big results! 🎯",
        ]
        suggestions = [
            "Aim for 150+ minutes of moderate exercise per week",
            "Reduce portion sizes and eat mindfully",
            "Cut back on sugary drinks and processed foods",
            "Add more vegetables and fiber to your meals",
            "Track your food intake to stay accountable",
            "Consider consulting a dietitian for personalized advice",
        ]
    else:
        category = "obese"
        color = "#ef4444"  # red
        messages = [
            "Let's work on this together! Small steps lead to big changes 🌱",
            "Your health is worth the effort - let's start today! 💪",
            "Time for a healthy transformation! You've got this! 🌟",
            "Every journey starts with one step - let's take it! 👟",
        ]
        suggestions = [
            "Consult a healthcare provider before starting any diet/exercise program",
            "Consider working with a registered dietitian",
            "Start with low-impact exercises like walking or swimming",
            "Focus on sustainable lifestyle changes, not quick fixes",
            "Join a support group or find an accountability partner",
            "Track your progress - celebrate small victories!",
            "Prioritize sleep and stress management",
        ]
    
    message = random.choice(messages)
    
    return {
        "bmi": bmi,
        "category": category,
        "message": message,
        "suggestions": suggestions,
        "color": color,
    }


def compare_bmi_records(current: dict, previous: dict) -> dict:
    """Compare two BMI records and provide feedback."""
    bmi_diff = round(current["bmi"] - previous["bmi"], 1)
    
    if abs(bmi_diff) < 0.1:
        trend = "stable"
        trend_message = "Your BMI has remained stable. Keep maintaining your healthy habits! 🎯"
    elif bmi_diff > 0:
        if current["category"] == "underweight" and previous["category"] == "underweight":
            trend = "improving"
            trend_message = f"Great progress! Your BMI increased by {bmi_diff}. Keep gaining healthily! 📈"
        elif current["category"] in ["overweight", "obese"]:
            trend = "needs_attention"
            trend_message = f"Your BMI increased by {bmi_diff}. Consider adjusting your diet and exercise. ⚠️"
        else:
            trend = "neutral"
            trend_message = f"Your BMI increased by {bmi_diff}. Monitor your progress. 📊"
    else:
        if current["category"] in ["overweight", "obese"]:
            trend = "improving"
            trend_message = f"Excellent! Your BMI decreased by {abs(bmi_diff)}. Keep up the great work! 📉"
        elif current["category"] == "underweight":
            trend = "needs_attention"
            trend_message = f"Your BMI decreased by {abs(bmi_diff)}. Make sure you're eating enough! ⚠️"
        else:
            trend = "neutral"
            trend_message = f"Your BMI decreased by {abs(bmi_diff)}. Stay healthy! 📊"
    
    return {
        "bmi_change": bmi_diff,
        "trend": trend,
        "trend_message": trend_message,
        "previous_bmi": previous["bmi"],
        "previous_category": previous["category"],
        "current_bmi": current["bmi"],
        "current_category": current["category"],
    }
