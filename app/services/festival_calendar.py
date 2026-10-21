"""Autonomous Festival Marketing Engine.

Inspired by Dhanda AI Marketing: automatically tracks major national, cultural,
and business celebration days, generates tailored branded festival greetings & offers,
and prepares automated publishing for Google Business Profile (GMB), Instagram, LinkedIn, and X.
"""
import datetime
from typing import Optional, Any
from app.services.poster_generator import generate_social_poster


# Master curated festival & high-impact business event calendar
FESTIVALS_CALENDAR = [
    {
        "id": "new_year",
        "name": "New Year 2026",
        "month": 1,
        "day": 1,
        "category": "Celebration",
        "greeting": "Wishing you and your family a prosperous, joyful, and successful New Year!",
        "theme_tag": "Happy New Year",
        "default_cta": "Celebrate With Us",
        "hashtags": ["#NewYear2026", "#FreshBeginnings", "#Success", "#Celebration"],
        "poster_style": "festival_newyear"
    },
    {
        "id": "republic_day",
        "name": "Republic Day",
        "month": 1,
        "day": 26,
        "category": "National",
        "greeting": "Honoring the spirit of unity, freedom, and sovereign progress this Republic Day.",
        "theme_tag": "Proud & United",
        "default_cta": "Explore Special Offers",
        "hashtags": ["#RepublicDay", "#ProudNation", "#UnityInDiversity", "#Freedom"],
        "poster_style": "festival_national"
    },
    {
        "id": "womens_day",
        "name": "International Women's Day",
        "month": 3,
        "day": 8,
        "category": "Observance",
        "greeting": "Celebrating the resilience, leadership, and remarkable achievements of women worldwide.",
        "theme_tag": "Empower & Inspire",
        "default_cta": "Honor Today",
        "hashtags": ["#WomensDay", "#InspireInclusion", "#WomenLeaders", "#Empowerment"],
        "poster_style": "quote_leadership"
    },
    {
        "id": "holi",
        "name": "Holi — Festival of Colors",
        "month": 3,
        "day": 25,
        "category": "Cultural",
        "greeting": "May your life be painted with colors of boundless happiness, peace, and vibrant success!",
        "theme_tag": "Joyful Colors",
        "default_cta": "Grab Holi Festive Deals",
        "hashtags": ["#HappyHoli", "#FestivalOfColors", "#JoyAndColor", "#FestiveOffers"],
        "poster_style": "festival_holi"
    },
    {
        "id": "eid_fitr",
        "name": "Eid al-Fitr",
        "month": 4,
        "day": 10,
        "category": "Religious",
        "greeting": "Eid Mubarak! May divine blessings fill your home with harmony, peace, and abundance.",
        "theme_tag": "Eid Mubarak",
        "default_cta": "Celebrate With Us",
        "hashtags": ["#EidMubarak", "#PeaceAndBlessings", "#Celebration", "#Joy"],
        "poster_style": "festival_eid"
    },
    {
        "id": "independence_day",
        "name": "Independence Day",
        "month": 8,
        "day": 15,
        "category": "National",
        "greeting": "Celebrating independence, innovation, and our collective drive toward greatness.",
        "theme_tag": "Saluting Freedom",
        "default_cta": "Freedom Sale Inside",
        "hashtags": ["#IndependenceDay", "#FreedomSale", "#ProudNation", "#Growth"],
        "poster_style": "festival_national"
    },
    {
        "id": "raksha_bandhan",
        "name": "Raksha Bandhan",
        "month": 8,
        "day": 28,
        "category": "Cultural",
        "greeting": "Celebrating the cherished bond of love, trust, and lifelong protection.",
        "theme_tag": "Bond of Love",
        "default_cta": "Gift Your Loved Ones",
        "hashtags": ["#RakshaBandhan", "#SiblingsLove", "#FestiveGifting", "#Celebration"],
        "poster_style": "festival_diwali"
    },
    {
        "id": "ganesh_chaturthi",
        "name": "Ganesh Chaturthi",
        "month": 9,
        "day": 16,
        "category": "Cultural",
        "greeting": "May Lord Ganesha remove all obstacles and shower your business with wisdom and prosperity.",
        "theme_tag": "Auspicious Beginnings",
        "default_cta": "Discover Auspicious Deals",
        "hashtags": ["#GaneshChaturthi", "#GanpatiBappaMorya", "#NewBeginnings", "#Blessings"],
        "poster_style": "festival_diwali"
    },
    {
        "id": "dussehra",
        "name": "Dussehra / Vijayadashami",
        "month": 10,
        "day": 12,
        "category": "Cultural",
        "greeting": "Celebrating the victory of light over darkness, truth over falsehood, and good over evil.",
        "theme_tag": "Triumph of Good",
        "default_cta": "Explore Vijay Specials",
        "hashtags": ["#HappyDussehra", "#VictoryOfGood", "#FestiveSeason", "#NewHorizons"],
        "poster_style": "festival_diwali"
    },
    {
        "id": "diwali",
        "name": "Diwali — Festival of Lights",
        "month": 11,
        "day": 1,
        "category": "Cultural",
        "greeting": "May the radiant glow of diyas illuminate your life with infinite health, wealth, and joy!",
        "theme_tag": "Shubh Deepavali",
        "default_cta": "Shop Grand Diwali Sale",
        "hashtags": ["#HappyDiwali", "#FestivalOfLights", "#Deepavali", "#DiwaliMegaSale", "#Prosperity"],
        "poster_style": "festival_diwali"
    },
    {
        "id": "christmas",
        "name": "Christmas Day",
        "month": 12,
        "day": 25,
        "category": "Celebration",
        "greeting": "Wishing you peace, warmth, and holiday magic this joyful Christmas season!",
        "theme_tag": "Merry Christmas",
        "default_cta": "Unwrap Holiday Discounts",
        "hashtags": ["#MerryChristmas", "#HolidayCheer", "#SeasonOfGiving", "#HolidayOffers"],
        "poster_style": "festival_newyear"
    }
]


def get_upcoming_festivals(limit: int = 5, ref_date: Optional[datetime.date] = None) -> list[dict[str, Any]]:
    """Returns the next upcoming festivals sorted by date proximity."""
    today = ref_date or datetime.date.today()
    current_year = today.year

    festival_instances = []
    for f in FESTIVALS_CALENDAR:
        # Determine occurrence in current or next year
        try:
            fest_date = datetime.date(current_year, f["month"], f["day"])
        except ValueError:
            fest_date = datetime.date(current_year, f["month"], min(f["day"], 28))

        if fest_date < today:
            fest_date = datetime.date(current_year + 1, f["month"], f["day"])

        days_left = (fest_date - today).days
        festival_instances.append({
            **f,
            "date": fest_date.isoformat(),
            "formatted_date": fest_date.strftime("%B %d, %Y"),
            "days_until": days_left
        })

    festival_instances.sort(key=lambda x: x["days_until"])
    return festival_instances[:limit]


def generate_festival_post(
    festival_id: str,
    brand_name: str,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    website: Optional[str] = None,
    custom_offer: Optional[str] = None
) -> dict[str, Any]:
    """Generates complete branded creative copy and poster for a festival."""
    festival = next((f for f in FESTIVALS_CALENDAR if f["id"] == festival_id), FESTIVALS_CALENDAR[0])

    headline = f"Warm {festival['name']} Wishes from {brand_name}!"
    offer_text = custom_offer or f"Special festive perks available for our valued patrons."
    
    copy = (
        f"{festival['greeting']}\n\n"
        f"At {brand_name}, we cherish celebrating this auspicious occasion with you. "
        f"{offer_text}\n\n"
        f"👉 Visit us or get in touch: {phone or website or 'Contact our team today.'}\n\n"
        f"{' '.join(festival['hashtags'])}"
    )

    data_uri, poster_path = generate_social_poster(
        brand=brand_name,
        headline=f"Happy {festival['name']}! {festival['greeting']}",
        platform="instagram",
        tone=festival["poster_style"],
        call_to_action=festival["default_cta"],
        subtitle=f"Celebrated with warm wishes by {brand_name}",
        business_phone=phone,
        business_address=address,
        business_website=website
    )

    return {
        "festival_id": festival["id"],
        "festival_name": festival["name"],
        "headline": headline,
        "copy": copy,
        "call_to_action": festival["default_cta"],
        "hashtags": festival["hashtags"],
        "poster_url": data_uri,
        "poster_path": poster_path,
        "poster_style": festival["poster_style"]
    }


class FestivalCalendarEngine:
    """High-level facade for autonomous festival marketing workflows."""

    def get_upcoming_festivals(self, limit: int = 10, days_ahead: int = 60, from_date: Optional[datetime.date] = None):
        return get_upcoming_festivals(limit=limit, ref_date=from_date)

    def generate_festival_post(
        self,
        festival_id: str,
        business_profile: dict[str, Any],
        custom_offer: Optional[str] = None
    ) -> dict[str, Any]:
        brand_name = business_profile.get("business_name") or "Your Business"
        phone = business_profile.get("phone")
        address = business_profile.get("address")
        website = business_profile.get("website")
        return generate_festival_post(
            festival_id=festival_id,
            brand_name=brand_name,
            phone=phone,
            address=address,
            website=website,
            custom_offer=custom_offer
        )


festival_engine = FestivalCalendarEngine()
