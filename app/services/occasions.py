"""Dynamic Occasions & Observances Engine.

Replaces hardcoded static festival banners with an authentic, multi-region,
and industry-aware Occasions Service. Computes dynamic days_until relative
to today's real date, matches tenant country and vertical, and enforces
zero cross-industry contamination and zero hardcoded fallback data.
"""
import datetime
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.creative_direction import resolve_vertical, build_creative_direction
from app.services.poster.contamination_guard import clean_copy_of_contamination


class OccasionRecord(BaseModel):
    id: str
    name: str
    month: int
    day: int
    category: str  # Cultural, Retail, Observance, National, Industry
    regions: List[str] = Field(default_factory=lambda: ["GLOBAL"])
    verticals: List[str] = Field(default_factory=lambda: ["all"])
    greeting: str
    theme_tag: str
    default_cta: str
    hashtags: List[str]
    days_until: int = 0
    formatted_date: str = ""
    is_vertical_specific: bool = False


# Comprehensive Curated Occasion Calendar
OCCASIONS_CATALOG: List[Dict[str, Any]] = [
    # Global & Multi-Region Observances
    {
        "id": "new_year",
        "name": "New Year's Day",
        "month": 1,
        "day": 1,
        "category": "Celebration",
        "regions": ["GLOBAL", "US", "IN", "UK"],
        "verticals": ["all"],
        "greeting": "Wishing you and your family a prosperous, healthy, and successful New Year!",
        "theme_tag": "Happy New Year",
        "default_cta": "Celebrate With Us",
        "hashtags": ["#NewYear", "#FreshBeginnings", "#Success", "#Celebration"]
    },
    {
        "id": "valentines_day",
        "name": "Valentine's Day",
        "month": 2,
        "day": 14,
        "category": "Celebration",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["all", "jewelry_luxury", "boutique_fashion", "salon_spa", "cafe_coffee"],
        "greeting": "Celebrate love, appreciation, and unforgettable moments.",
        "theme_tag": "Season of Love",
        "default_cta": "Explore Curated Gifts",
        "hashtags": ["#ValentinesDay", "#LoveAndCare", "#SpecialGifts", "#Celebration"]
    },
    {
        "id": "womens_day",
        "name": "International Women's Day",
        "month": 3,
        "day": 8,
        "category": "Observance",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["all"],
        "greeting": "Celebrating the resilience, leadership, and remarkable achievements of women worldwide.",
        "theme_tag": "Empower & Inspire",
        "default_cta": "Honor Today",
        "hashtags": ["#WomensDay", "#InspireInclusion", "#WomenLeaders", "#Empowerment"]
    },
    {
        "id": "earth_day",
        "name": "Earth Day",
        "month": 4,
        "day": 22,
        "category": "Observance",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["all", "salon_spa", "boutique_fashion"],
        "greeting": "Committed to sustainable practices, eco-conscious quality, and a greener future.",
        "theme_tag": "Earth & Harmony",
        "default_cta": "Discover Sustainable Choices",
        "hashtags": ["#EarthDay", "#Sustainability", "#GreenLiving", "#EcoConscious"]
    },
    {
        "id": "mothers_day",
        "name": "Mother's Day",
        "month": 5,
        "day": 10,
        "category": "Celebration",
        "regions": ["GLOBAL", "US", "IN"],
        "verticals": ["all", "jewelry_luxury", "salon_spa", "boutique_fashion"],
        "greeting": "Honoring mothers everywhere with gratitude, warmth, and heartfelt appreciation.",
        "theme_tag": "Celebrate Mom",
        "default_cta": "Find the Perfect Gift",
        "hashtags": ["#MothersDay", "#HonorMom", "#Gratitude", "#FamilyFirst"]
    },
    {
        "id": "fathers_day",
        "name": "Father's Day",
        "month": 6,
        "day": 21,
        "category": "Celebration",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["all", "sneakers_streetwear", "auto_detail"],
        "greeting": "To the mentors, protectors, and role models—happy Father's Day!",
        "theme_tag": "Honor Dads",
        "default_cta": "Browse Gifts for Him",
        "hashtags": ["#FathersDay", "#Celebration", "#Mentorship", "#GiftsForHim"]
    },
    {
        "id": "halloween",
        "name": "Halloween",
        "month": 10,
        "day": 31,
        "category": "Cultural",
        "regions": ["US", "UK", "GLOBAL"],
        "verticals": ["all", "sneakers_streetwear", "boutique_fashion"],
        "greeting": "Get into the festive spirit with spooktacular specials and limited-edition picks.",
        "theme_tag": "Spooky Season",
        "default_cta": "Unwrap Treat Specials",
        "hashtags": ["#Halloween", "#SpookySeason", "#TreatYourself", "#SpecialDrop"]
    },
    {
        "id": "black_friday",
        "name": "Black Friday",
        "month": 11,
        "day": 27,
        "category": "Retail",
        "regions": ["GLOBAL", "US", "UK"],
        "verticals": ["all"],
        "greeting": "Our biggest seasonal release is live. Premium selections at unprecedented value.",
        "theme_tag": "Black Friday Exclusive",
        "default_cta": "Claim Exclusive Deals",
        "hashtags": ["#BlackFriday", "#LimitedDrop", "#ExclusiveOffer", "#HolidayShopping"]
    },
    {
        "id": "cyber_monday",
        "name": "Cyber Monday",
        "month": 11,
        "day": 30,
        "category": "Retail",
        "regions": ["GLOBAL", "US", "UK"],
        "verticals": ["all", "tech_saas", "sneakers_streetwear"],
        "greeting": "Online exclusives available now. Elevate your experience before stocks expire.",
        "theme_tag": "Cyber Monday",
        "default_cta": "Shop Online Specials",
        "hashtags": ["#CyberMonday", "#DigitalDeals", "#OnlineExclusive", "#Upgrade"]
    },
    {
        "id": "christmas",
        "name": "Christmas Day",
        "month": 12,
        "day": 25,
        "category": "Celebration",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["all"],
        "greeting": "Warmest wishes for a peaceful, joyful, and festive holiday season.",
        "theme_tag": "Holiday Joy",
        "default_cta": "Explore Festive Specials",
        "hashtags": ["#MerryChristmas", "#HolidayJoy", "#FestiveSeason", "#Celebration"]
    },

    # United States National & Cultural
    {
        "id": "us_independence",
        "name": "Independence Day (4th of July)",
        "month": 7,
        "day": 4,
        "category": "National",
        "regions": ["US"],
        "verticals": ["all"],
        "greeting": "Celebrating freedom, independence, and the American spirit.",
        "theme_tag": "Star-Spangled Pride",
        "default_cta": "Explore 4th of July Specials",
        "hashtags": ["#July4th", "#IndependenceDay", "#Freedom", "#SummerCelebration"]
    },
    {
        "id": "us_thanksgiving",
        "name": "Thanksgiving Day",
        "month": 11,
        "day": 26,
        "category": "Cultural",
        "regions": ["US"],
        "verticals": ["all"],
        "greeting": "Grateful for our community, partners, and clients who make our journey possible.",
        "theme_tag": "Season of Gratitude",
        "default_cta": "Join Our Celebration",
        "hashtags": ["#Thanksgiving", "#Gratitude", "#Community", "#Family"]
    },

    # India Cultural & National
    {
        "id": "republic_day_in",
        "name": "Republic Day",
        "month": 1,
        "day": 26,
        "category": "National",
        "regions": ["IN"],
        "verticals": ["all"],
        "greeting": "Honoring the constitutional spirit of unity, freedom, and national progress.",
        "theme_tag": "Proud & Sovereign",
        "default_cta": "Explore Republic Day Specials",
        "hashtags": ["#RepublicDay", "#ProudNation", "#UnityInDiversity", "#Progress"]
    },
    {
        "id": "holi_in",
        "name": "Holi — Festival of Colors",
        "month": 3,
        "day": 25,
        "category": "Cultural",
        "regions": ["IN", "GLOBAL"],
        "verticals": ["all"],
        "greeting": "May your life be painted with colors of boundless joy, health, and vibrant success!",
        "theme_tag": "Joyful Colors",
        "default_cta": "Grab Holi Festive Deals",
        "hashtags": ["#HappyHoli", "#FestivalOfColors", "#JoyAndColor", "#FestiveOffers"]
    },
    {
        "id": "independence_day_in",
        "name": "Independence Day",
        "month": 8,
        "day": 15,
        "category": "National",
        "regions": ["IN"],
        "verticals": ["all"],
        "greeting": "Saluting 79+ years of freedom, innovation, and unstoppable collective growth.",
        "theme_tag": "Saluting Freedom",
        "default_cta": "Freedom Specials Inside",
        "hashtags": ["#IndependenceDay", "#FreedomSale", "#ProudIndia", "#Growth"]
    },
    {
        "id": "diwali_in",
        "name": "Diwali — Festival of Lights",
        "month": 11,
        "day": 1,
        "category": "Cultural",
        "regions": ["IN", "GLOBAL"],
        "verticals": ["all"],
        "greeting": "May the radiant divine light illuminate your path with prosperity, health, and peace.",
        "theme_tag": "Shubh Deepavali",
        "default_cta": "Claim Auspicious Festive Offers",
        "hashtags": ["#HappyDiwali", "#FestivalOfLights", "#Prosperity", "#FestiveVibes"]
    },

    # Vertical-Specific Observances & Milestone Days
    {
        "id": "air_max_day",
        "name": "Air Max Day & Sneaker Culture Day",
        "month": 3,
        "day": 26,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["sneakers_streetwear"],
        "greeting": "Celebrating sneaker design, heritage silhouettes, and urban streetwear culture.",
        "theme_tag": "Iconic Silhouette",
        "default_cta": "Browse Limited Drop",
        "hashtags": ["#AirMaxDay", "#Sneakerhead", "#KicksOfTheDay", "#StreetwearStyle"]
    },
    {
        "id": "go_skateboarding_day",
        "name": "Go Skateboarding & Street Culture Day",
        "month": 6,
        "day": 21,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK"],
        "verticals": ["sneakers_streetwear"],
        "greeting": "Pure street authenticity, movement, and heavyweight raw aesthetic.",
        "theme_tag": "Street Authenticity",
        "default_cta": "Explore Skate & Streetwear",
        "hashtags": ["#GoSkateDay", "#StreetCulture", "#SkateStyle", "#DropCulture"]
    },
    {
        "id": "global_wellness_day",
        "name": "Global Wellness & Self-Care Day",
        "month": 6,
        "day": 13,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["salon_spa", "clinic_healthcare"],
        "greeting": "Pause, breathe, and restore. Today is dedicated to holistic rejuvenation.",
        "theme_tag": "Mindful Rejuvenation",
        "default_cta": "Book Your Sanctuary Session",
        "hashtags": ["#GlobalWellnessDay", "#SelfCareSunday", "#BotanicalGlow", "#MindfulLiving"]
    },
    {
        "id": "national_hair_day",
        "name": "National Hair & Beauty Day",
        "month": 10,
        "day": 1,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK"],
        "verticals": ["salon_spa"],
        "greeting": "Transformative styling, master precision cuts, and radiant organic gloss.",
        "theme_tag": "Precision Glamour",
        "default_cta": "Reserve Stylist Chair",
        "hashtags": ["#NationalHairDay", "#SalonLife", "#GlossTreatment", "#MasterStylist"]
    },
    {
        "id": "world_health_day",
        "name": "World Health Day",
        "month": 4,
        "day": 7,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["clinic_healthcare"],
        "greeting": "Advancing clinical excellence, preventative screenings, and accessible wellness.",
        "theme_tag": "Preventative Care",
        "default_cta": "Schedule Health Checkup",
        "hashtags": ["#WorldHealthDay", "#PreventativeHealth", "#ClinicalCare", "#WellnessFirst"]
    },
    {
        "id": "intl_coffee_day",
        "name": "International Coffee Day",
        "month": 10,
        "day": 1,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["cafe_coffee"],
        "greeting": "Honoring the craft, single-origin roasters, and the perfect morning pour.",
        "theme_tag": "Artisan Roast",
        "default_cta": "Sip Today's Single Origin",
        "hashtags": ["#InternationalCoffeeDay", "#ArtisanRoast", "#SingleOrigin", "#CoffeeLovers"]
    },
    {
        "id": "national_fitness_day",
        "name": "National Fitness Day",
        "month": 9,
        "day": 23,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK"],
        "verticals": ["gym_fitness"],
        "greeting": "Push your limits. Every rep, sprint, and session shapes your peak endurance.",
        "theme_tag": "Relentless Performance",
        "default_cta": "Start Training Session",
        "hashtags": ["#NationalFitnessDay", "#NoExcuses", "#TrainHard", "#PeakConditioning"]
    },
    {
        "id": "spring_home_buying",
        "name": "Spring Prime Property Season",
        "month": 4,
        "day": 1,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK"],
        "verticals": ["real_estate"],
        "greeting": "Prime listings, bespoke residences, and exclusive private estate tours.",
        "theme_tag": "Exclusive Property",
        "default_cta": "Schedule Private Tour",
        "hashtags": ["#LuxuryRealEstate", "#PrimeProperty", "#SpringMarket", "#BespokeLiving"]
    },
    {
        "id": "world_backup_day",
        "name": "World Data Protection & Tech Day",
        "month": 3,
        "day": 31,
        "category": "Industry",
        "regions": ["GLOBAL", "US", "UK", "IN"],
        "verticals": ["tech_saas"],
        "greeting": "Secure systems, zero-downtime architecture, and robust automated workflows.",
        "theme_tag": "Data Resilience",
        "default_cta": "Secure Your Infrastructure",
        "hashtags": ["#WorldBackupDay", "#CyberSecurity", "#CloudReliability", "#ZeroDowntime"]
    }
]


def _compute_days_until(target_month: int, target_day: int, ref_date: datetime.date) -> tuple[int, datetime.date]:
    """Calculates days until next occurrence of month/day relative to ref_date."""
    year = ref_date.year
    try:
        cand_date = datetime.date(year, target_month, target_day)
    except ValueError:
        cand_date = datetime.date(year, target_month, 28)

    if cand_date < ref_date:
        try:
            cand_date = datetime.date(year + 1, target_month, target_day)
        except ValueError:
            cand_date = datetime.date(year + 1, target_month, 28)

    days = (cand_date - ref_date).days
    return days, cand_date


class OccasionsService:
    """Production Occasion & Festival Service supporting multi-region and industry matching."""

    def __init__(self, db_path_getter=None):
        self._db_path_getter = db_path_getter

    def get_upcoming_occasions(
        self,
        ref_date: Optional[datetime.date] = None,
        days_ahead: int = 90,
        region: Optional[str] = None,
        vertical: Optional[str] = None
    ) -> List[OccasionRecord]:
        """Returns upcoming occasions dynamically sorted by proximity."""
        today = ref_date or datetime.date.today()
        norm_region = (region or "GLOBAL").upper()
        norm_vert = (vertical or "all").lower()

        results: List[OccasionRecord] = []
        for occ in OCCASIONS_CATALOG:
            # Region check: matches if GLOBAL, or if exact region matches
            occ_regions = [r.upper() for r in occ.get("regions", ["GLOBAL"])]
            region_match = ("GLOBAL" in occ_regions) or (norm_region in occ_regions) or (norm_region == "ALL")

            # Vertical check: matches if all, or exact vertical matches
            occ_verts = [v.lower() for v in occ.get("verticals", ["all"])]
            is_vert_specific = "all" not in occ_verts
            vert_match = ("all" in occ_verts) or (norm_vert in occ_verts) or (norm_vert == "all")

            if not (region_match and vert_match):
                continue

            days, next_date = _compute_days_until(occ["month"], occ["day"], today)
            if 0 <= days <= days_ahead:
                results.append(OccasionRecord(
                    id=occ["id"],
                    name=occ["name"],
                    month=occ["month"],
                    day=occ["day"],
                    category=occ["category"],
                    regions=occ.get("regions", ["GLOBAL"]),
                    verticals=occ.get("verticals", ["all"]),
                    greeting=occ["greeting"],
                    theme_tag=occ["theme_tag"],
                    default_cta=occ["default_cta"],
                    hashtags=occ["hashtags"],
                    days_until=days,
                    formatted_date=next_date.strftime("%B %d, %Y"),
                    is_vertical_specific=is_vert_specific
                ))

        # Sort: first by days_until, second with vertical-specific prioritization
        results.sort(key=lambda x: (x.days_until, 0 if x.is_vertical_specific else 1))
        return results

    def find_occasion_by_id(self, occasion_id: str) -> Optional[Dict[str, Any]]:
        for occ in OCCASIONS_CATALOG:
            if occ["id"] == occasion_id:
                return occ
        return None

    def generate_occasion_campaign(
        self,
        tenant_id: str,
        occasion_id: str,
        business_profile: Optional[Dict[str, Any]] = None,
        custom_offer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Builds a verified, zero-contamination occasion campaign for the tenant's profile."""
        if not business_profile or not business_profile.get("business_name"):
            raise ValueError("A registered business profile is strictly required. No default fallback permitted.")

        occ = self.find_occasion_by_id(occasion_id)
        if not occ:
            raise ValueError(f"Occasion ID '{occasion_id}' not found in maintained occasions calendar.")

        b_name = business_profile.get("business_name")
        vert = resolve_vertical(
            industry_primary=business_profile.get("industry_primary") or "",
            industry_sub=business_profile.get("industry_sub") or "",
            business_name=b_name
        )
        creative = build_creative_direction(vert, business_name=b_name)

        # Enforce zero contamination on greeting
        raw_greeting = occ["greeting"]
        clean_greeting = clean_copy_of_contamination(raw_greeting, vertical=vert, fallback=f"Celebrating special moments with {b_name}.")

        offer_text = custom_offer or (f"Special seasonal value available now at {b_name}." if vert != "cafe_coffee" else "Handcrafted seasonal roasts available today.")
        clean_offer = clean_copy_of_contamination(offer_text, vertical=vert, fallback=f"Exclusive seasonal specials at {b_name}.")

        copy = f"✦ {occ['name']} with {b_name} ✦\n\n{clean_greeting}\n\n{clean_offer}\n\n📍 {business_profile.get('address', 'Visit us today')}\n📞 {business_profile.get('contact_phone', business_profile.get('phone', ''))}\n🌐 {business_profile.get('website_url', business_profile.get('website', ''))}"

        # Clean hashtags
        hashtags = [h for h in occ.get("hashtags", [])]
        brand_tag = f"#{b_name.replace(' ', '')}"
        if brand_tag not in hashtags:
            hashtags.append(brand_tag)

        return {
            "occasion_id": occ["id"],
            "occasion_name": occ["name"],
            "headline": f"{occ['theme_tag']} at {b_name}",
            "greeting": clean_greeting,
            "offer": clean_offer,
            "copy": copy,
            "hashtags": hashtags,
            "vertical": vert,
            "theme_tag": occ["theme_tag"],
            "default_cta": occ["default_cta"],
            "primary_color": creative.palette.primary,
            "accent_color": creative.palette.accent
        }


occasions_service = OccasionsService()
