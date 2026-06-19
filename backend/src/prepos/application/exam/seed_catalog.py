"""UPSC CSE domain catalog seed builder per EXAM_DOMAIN_SPECIFICATION.md."""

from __future__ import annotations

from typing import TypedDict
from uuid import NAMESPACE_URL, uuid5

from prepos.domain.exam.value_objects import derive_exam_stages

EXAM_ID = "upsc_cse"
CATALOG_VERSION = "1.0.0"
EXAM_CODE = "upsc_cse"

SubjectTargetCounts: dict[str, int] = {
    "history": 45,
    "art_culture": 30,
    "geography": 40,
    "polity": 65,
    "economy": 50,
    "environment": 35,
    "science_technology": 40,
    "international_relations": 25,
    "governance": 20,
    "social_justice": 20,
    "society": 20,
    "internal_security": 25,
    "disaster_management": 12,
    "agriculture": 20,
    "ethics": 25,
    "essay": 15,
    "current_affairs": 30,
    "csat": 20,
}


class ConceptSpec(TypedDict, total=False):
    slug: str
    name: str
    concept_type: str
    parent_slug: str | None
    prelims_relevance: int | None
    mains_relevance: int | None
    current_affairs_linkable: bool
    pyq_mappable: bool
    difficulty: int
    tags: list[str]


class TopicSpec(TypedDict):
    slug: str
    name: str
    prelims_relevance: int
    mains_relevance: int


class SubjectSpec(TypedDict):
    slug: str
    name: str
    prelims_applicable: bool
    mains_applicable: bool
    topics: list[TopicSpec]


SUBJECTS: list[SubjectSpec] = [
    {
        "slug": "history",
        "name": "History",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "ancient", "name": "Ancient History", "prelims_relevance": 70, "mains_relevance": 75},
            {"slug": "medieval", "name": "Medieval History", "prelims_relevance": 60, "mains_relevance": 65},
            {"slug": "modern", "name": "Modern History", "prelims_relevance": 95, "mains_relevance": 95},
            {"slug": "freedom_struggle", "name": "Freedom Struggle", "prelims_relevance": 90, "mains_relevance": 95},
            {"slug": "post_independence", "name": "Post-Independence India", "prelims_relevance": 50, "mains_relevance": 80},
            {"slug": "world_history", "name": "World History", "prelims_relevance": 40, "mains_relevance": 70},
        ],
    },
    {
        "slug": "art_culture",
        "name": "Art & Culture",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "architecture", "name": "Architecture", "prelims_relevance": 75, "mains_relevance": 80},
            {"slug": "sculpture_painting", "name": "Sculpture & Painting", "prelims_relevance": 65, "mains_relevance": 75},
            {"slug": "literature", "name": "Literature & Philosophy", "prelims_relevance": 55, "mains_relevance": 70},
            {"slug": "performing_arts", "name": "Performing Arts", "prelims_relevance": 60, "mains_relevance": 65},
            {"slug": "heritage_conservation", "name": "Heritage & Conservation", "prelims_relevance": 70, "mains_relevance": 85},
        ],
    },
    {
        "slug": "geography",
        "name": "Geography",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "physical", "name": "Physical Geography", "prelims_relevance": 85, "mains_relevance": 70},
            {"slug": "indian_geography", "name": "Indian Geography", "prelims_relevance": 90, "mains_relevance": 85},
            {"slug": "world_geography", "name": "World Geography", "prelims_relevance": 70, "mains_relevance": 60},
            {"slug": "human_economic", "name": "Human & Economic Geography", "prelims_relevance": 75, "mains_relevance": 75},
            {"slug": "climatology", "name": "Climatology", "prelims_relevance": 80, "mains_relevance": 65},
            {"slug": "geomorphology", "name": "Geomorphology", "prelims_relevance": 75, "mains_relevance": 60},
            {"slug": "oceanography", "name": "Oceanography", "prelims_relevance": 65, "mains_relevance": 55},
            {"slug": "resources", "name": "Resources & Industries", "prelims_relevance": 70, "mains_relevance": 70},
        ],
    },
    {
        "slug": "polity",
        "name": "Polity",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "constitution_basics", "name": "Constitution — Basics & Making", "prelims_relevance": 85, "mains_relevance": 80},
            {"slug": "fundamental_rights", "name": "Fundamental Rights", "prelims_relevance": 95, "mains_relevance": 95},
            {"slug": "dpsp", "name": "Directive Principles (DPSP)", "prelims_relevance": 80, "mains_relevance": 90},
            {"slug": "fundamental_duties", "name": "Fundamental Duties", "prelims_relevance": 60, "mains_relevance": 70},
            {"slug": "union_executive", "name": "Union Executive", "prelims_relevance": 85, "mains_relevance": 85},
            {"slug": "parliament", "name": "Parliament", "prelims_relevance": 90, "mains_relevance": 90},
            {"slug": "judiciary", "name": "Judiciary", "prelims_relevance": 90, "mains_relevance": 90},
            {"slug": "federalism", "name": "Federalism", "prelims_relevance": 85, "mains_relevance": 90},
            {"slug": "local_government", "name": "Local Government", "prelims_relevance": 75, "mains_relevance": 80},
            {"slug": "constitutional_bodies", "name": "Constitutional Bodies", "prelims_relevance": 80, "mains_relevance": 75},
            {"slug": "non_constitutional_bodies", "name": "Non-Constitutional Bodies", "prelims_relevance": 75, "mains_relevance": 70},
            {"slug": "amendments", "name": "Constitutional Amendments", "prelims_relevance": 80, "mains_relevance": 75},
            {"slug": "emergency", "name": "Emergency Provisions", "prelims_relevance": 70, "mains_relevance": 80},
            {"slug": "center_state_relations", "name": "Centre–State Relations", "prelims_relevance": 80, "mains_relevance": 85},
        ],
    },
    {
        "slug": "economy",
        "name": "Economy",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "national_income", "name": "National Income & Growth", "prelims_relevance": 80, "mains_relevance": 85},
            {"slug": "inflation", "name": "Inflation", "prelims_relevance": 85, "mains_relevance": 85},
            {"slug": "fiscal_policy", "name": "Fiscal Policy", "prelims_relevance": 85, "mains_relevance": 90},
            {"slug": "monetary_policy", "name": "Monetary Policy", "prelims_relevance": 90, "mains_relevance": 90},
            {"slug": "banking", "name": "Banking & Financial System", "prelims_relevance": 90, "mains_relevance": 85},
            {"slug": "budget", "name": "Budget & Taxation", "prelims_relevance": 85, "mains_relevance": 90},
            {"slug": "external_sector", "name": "External Sector", "prelims_relevance": 80, "mains_relevance": 85},
            {"slug": "planning", "name": "Planning & Development", "prelims_relevance": 70, "mains_relevance": 75},
            {"slug": "agriculture_economics", "name": "Agriculture Economics", "prelims_relevance": 75, "mains_relevance": 85},
            {"slug": "industry_services", "name": "Industry & Services", "prelims_relevance": 70, "mains_relevance": 80},
            {"slug": "inclusive_growth", "name": "Inclusive Growth & Employment", "prelims_relevance": 65, "mains_relevance": 85},
            {"slug": "international_economics", "name": "International Economics", "prelims_relevance": 60, "mains_relevance": 70},
        ],
    },
    {
        "slug": "environment",
        "name": "Environment & Ecology",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "ecology_basics", "name": "Ecology Basics", "prelims_relevance": 85, "mains_relevance": 75},
            {"slug": "biodiversity", "name": "Biodiversity", "prelims_relevance": 90, "mains_relevance": 85},
            {"slug": "climate_change", "name": "Climate Change", "prelims_relevance": 90, "mains_relevance": 90},
            {"slug": "pollution", "name": "Pollution & Waste", "prelims_relevance": 85, "mains_relevance": 80},
            {"slug": "conservation", "name": "Conservation & Protected Areas", "prelims_relevance": 85, "mains_relevance": 85},
            {"slug": "environmental_laws", "name": "Environmental Laws & Institutions", "prelims_relevance": 80, "mains_relevance": 85},
            {"slug": "sustainable_development", "name": "Sustainable Development", "prelims_relevance": 75, "mains_relevance": 85},
        ],
    },
    {
        "slug": "science_technology",
        "name": "Science & Technology",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "space", "name": "Space Technology", "prelims_relevance": 80, "mains_relevance": 75},
            {"slug": "it_digital", "name": "IT & Digital Technology", "prelims_relevance": 85, "mains_relevance": 80},
            {"slug": "biotechnology", "name": "Biotechnology & Health", "prelims_relevance": 80, "mains_relevance": 75},
            {"slug": "energy", "name": "Energy Science", "prelims_relevance": 75, "mains_relevance": 80},
            {"slug": "defence", "name": "Defence Technology", "prelims_relevance": 70, "mains_relevance": 70},
            {"slug": "materials_nano", "name": "Materials & Nanotechnology", "prelims_relevance": 60, "mains_relevance": 60},
            {"slug": "general_science", "name": "General Science (Physics/Chem/Bio)", "prelims_relevance": 90, "mains_relevance": 50},
        ],
    },
    {
        "slug": "international_relations",
        "name": "International Relations",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "india_foreign_policy", "name": "India Foreign Policy", "prelims_relevance": 40, "mains_relevance": 90},
            {"slug": "bilateral", "name": "Bilateral Relations", "prelims_relevance": 35, "mains_relevance": 85},
            {"slug": "regional", "name": "Regional Groupings", "prelims_relevance": 40, "mains_relevance": 80},
            {"slug": "global_institutions", "name": "Global Institutions", "prelims_relevance": 50, "mains_relevance": 85},
            {"slug": "conflicts", "name": "Conflicts & Geopolitics", "prelims_relevance": 45, "mains_relevance": 80},
        ],
    },
    {
        "slug": "governance",
        "name": "Governance",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "civil_services", "name": "Civil Services & Reforms", "prelims_relevance": 30, "mains_relevance": 85},
            {"slug": "e_governance", "name": "E-Governance", "prelims_relevance": 40, "mains_relevance": 85},
            {"slug": "transparency_accountability", "name": "Transparency & Accountability", "prelims_relevance": 35, "mains_relevance": 90},
            {"slug": "citizen_charters", "name": "Citizen Charters & RTI", "prelims_relevance": 50, "mains_relevance": 85},
            {"slug": "public_policy", "name": "Public Policy", "prelims_relevance": 30, "mains_relevance": 90},
        ],
    },
    {
        "slug": "social_justice",
        "name": "Social Justice",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "welfare_schemes", "name": "Welfare Schemes", "prelims_relevance": 60, "mains_relevance": 90},
            {"slug": "vulnerable_sections", "name": "Vulnerable Sections", "prelims_relevance": 55, "mains_relevance": 90},
            {"slug": "education_health", "name": "Education & Health", "prelims_relevance": 50, "mains_relevance": 85},
            {"slug": "poverty_hunger", "name": "Poverty & Hunger", "prelims_relevance": 55, "mains_relevance": 85},
        ],
    },
    {
        "slug": "society",
        "name": "Society",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "indian_society_structure", "name": "Indian Society Structure", "prelims_relevance": 30, "mains_relevance": 85},
            {"slug": "population_urbanization", "name": "Population & Urbanization", "prelims_relevance": 45, "mains_relevance": 80},
            {"slug": "women_children", "name": "Women & Children", "prelims_relevance": 40, "mains_relevance": 85},
            {"slug": "globalization_society", "name": "Globalization & Society", "prelims_relevance": 35, "mains_relevance": 80},
            {"slug": "social_movements", "name": "Social Movements", "prelims_relevance": 40, "mains_relevance": 85},
        ],
    },
    {
        "slug": "internal_security",
        "name": "Internal Security",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "extremism", "name": "Extremism & Left-Wing Extremism", "prelims_relevance": 40, "mains_relevance": 85},
            {"slug": "terrorism", "name": "Terrorism & Radicalization", "prelims_relevance": 45, "mains_relevance": 90},
            {"slug": "cyber_security", "name": "Cyber Security", "prelims_relevance": 50, "mains_relevance": 85},
            {"slug": "border_management", "name": "Border Management", "prelims_relevance": 40, "mains_relevance": 80},
            {"slug": "organized_crime", "name": "Organized Crime & Money Laundering", "prelims_relevance": 35, "mains_relevance": 75},
            {"slug": "security_forces", "name": "Security Forces & Agencies", "prelims_relevance": 50, "mains_relevance": 80},
        ],
    },
    {
        "slug": "disaster_management",
        "name": "Disaster Management",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "framework", "name": "Disaster Management Framework", "prelims_relevance": 45, "mains_relevance": 85},
            {"slug": "types_mitigation", "name": "Disaster Types & Mitigation", "prelims_relevance": 50, "mains_relevance": 85},
            {"slug": "institutions", "name": "Institutions (NDMA/NDRF)", "prelims_relevance": 45, "mains_relevance": 80},
        ],
    },
    {
        "slug": "agriculture",
        "name": "Agriculture",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "crops_cropping", "name": "Crops & Cropping Systems", "prelims_relevance": 55, "mains_relevance": 80},
            {"slug": "irrigation", "name": "Irrigation & Water Use", "prelims_relevance": 50, "mains_relevance": 75},
            {"slug": "subsidies_food", "name": "Subsidies & Food Security", "prelims_relevance": 55, "mains_relevance": 85},
            {"slug": "agri_technology", "name": "Agricultural Technology", "prelims_relevance": 45, "mains_relevance": 75},
            {"slug": "rural_development", "name": "Rural Development", "prelims_relevance": 40, "mains_relevance": 80},
        ],
    },
    {
        "slug": "ethics",
        "name": "Ethics",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "theories", "name": "Ethical Theories", "prelims_relevance": 0, "mains_relevance": 90},
            {"slug": "integrity_aptitude", "name": "Integrity & Aptitude", "prelims_relevance": 0, "mains_relevance": 95},
            {"slug": "attitude", "name": "Attitude", "prelims_relevance": 0, "mains_relevance": 85},
            {"slug": "emotional_intelligence", "name": "Emotional Intelligence", "prelims_relevance": 0, "mains_relevance": 80},
            {"slug": "public_service_values", "name": "Public Service Values", "prelims_relevance": 0, "mains_relevance": 95},
            {"slug": "probity_governance", "name": "Probity in Governance", "prelims_relevance": 0, "mains_relevance": 90},
            {"slug": "case_studies", "name": "Case Studies", "prelims_relevance": 0, "mains_relevance": 95},
        ],
    },
    {
        "slug": "essay",
        "name": "Essay",
        "prelims_applicable": False,
        "mains_applicable": True,
        "topics": [
            {"slug": "philosophical", "name": "Philosophical Essays", "prelims_relevance": 0, "mains_relevance": 90},
            {"slug": "society_development", "name": "Society & Development", "prelims_relevance": 0, "mains_relevance": 90},
            {"slug": "polity_governance", "name": "Polity & Governance", "prelims_relevance": 0, "mains_relevance": 85},
            {"slug": "economy_environment", "name": "Economy & Environment", "prelims_relevance": 0, "mains_relevance": 85},
            {"slug": "ethics_humanity", "name": "Ethics & Humanity", "prelims_relevance": 0, "mains_relevance": 90},
        ],
    },
    {
        "slug": "current_affairs",
        "name": "Current Affairs",
        "prelims_applicable": True,
        "mains_applicable": True,
        "topics": [
            {"slug": "national", "name": "National Affairs", "prelims_relevance": 90, "mains_relevance": 85},
            {"slug": "international", "name": "International Affairs", "prelims_relevance": 85, "mains_relevance": 85},
            {"slug": "economy", "name": "Economic Affairs", "prelims_relevance": 85, "mains_relevance": 85},
            {"slug": "science_env", "name": "Science, Environment & Tech Affairs", "prelims_relevance": 80, "mains_relevance": 80},
            {"slug": "polity_governance", "name": "Polity & Governance Affairs", "prelims_relevance": 85, "mains_relevance": 90},
            {"slug": "reports_indices", "name": "Reports, Indices & Summits", "prelims_relevance": 75, "mains_relevance": 75},
        ],
    },
    {
        "slug": "csat",
        "name": "CSAT",
        "prelims_applicable": True,
        "mains_applicable": False,
        "topics": [
            {"slug": "comprehension", "name": "Comprehension", "prelims_relevance": 90, "mains_relevance": 0},
            {"slug": "logical_reasoning", "name": "Logical Reasoning", "prelims_relevance": 90, "mains_relevance": 0},
            {"slug": "quantitative_aptitude", "name": "Quantitative Aptitude", "prelims_relevance": 90, "mains_relevance": 0},
            {"slug": "decision_making", "name": "Decision Making", "prelims_relevance": 85, "mains_relevance": 0},
        ],
    },
]

TRACK_DEFINITIONS: list[dict[str, object]] = [
    {
        "track_code": "prelims_gs1",
        "track_name": "Prelims GS Paper I",
        "stage": "prelims",
        "subject_slugs": [
            "history",
            "geography",
            "polity",
            "economy",
            "environment",
            "science_technology",
            "current_affairs",
        ],
    },
    {
        "track_code": "prelims_csat",
        "track_name": "Prelims CSAT Paper II",
        "stage": "prelims",
        "subject_slugs": ["csat"],
    },
    {
        "track_code": "mains_gs1",
        "track_name": "Mains GS Paper I",
        "stage": "mains",
        "subject_slugs": ["history", "art_culture", "geography", "society"],
    },
    {
        "track_code": "mains_gs2",
        "track_name": "Mains GS Paper II",
        "stage": "mains",
        "subject_slugs": ["polity", "governance", "social_justice", "international_relations"],
    },
    {
        "track_code": "mains_gs3",
        "track_name": "Mains GS Paper III",
        "stage": "mains",
        "subject_slugs": [
            "economy",
            "agriculture",
            "environment",
            "science_technology",
            "internal_security",
            "disaster_management",
        ],
    },
    {
        "track_code": "mains_gs4",
        "track_name": "Mains GS Paper IV",
        "stage": "mains",
        "subject_slugs": ["ethics"],
    },
    {
        "track_code": "mains_essay",
        "track_name": "Mains Essay Paper",
        "stage": "essay",
        "subject_slugs": ["essay"],
    },
]

# slug, name, concept_type, parent_slug (optional)
ConceptTuple = tuple[str, str, str] | tuple[str, str, str, str | None]

CONCEPTS_BY_TOPIC: dict[str, list[tuple[str, str, str] | tuple[str, str, str, str | None]]] = {'agriculture.agri_technology': [('precision_farming', 'Precision Farming', 'process'),
                                 ('bio_fortification', 'Bio-fortification', 'process'),
                                 ('farm_mechanization', 'Farm Mechanization', 'process'),
                                 ('overview', 'Agricultural Technology — Overview', 'definition')],
 'agriculture.crops_cropping': [('cropping_patterns', 'Cropping Patterns in India', 'definition'),
                                ('green_revolution', 'Green Revolution', 'event'),
                                ('crop_diversification', 'Crop Diversification', 'process'),
                                ('overview', 'Crops and Cropping — Overview', 'definition')],
 'agriculture.irrigation': [('irrigation_types', 'Irrigation Types', 'definition'),
                            ('water_use_efficiency', 'Water Use Efficiency', 'process'),
                            ('pmksy', 'PM Krishi Sinchayee Yojana', 'policy_scheme'),
                            ('overview', 'Irrigation — Overview', 'definition')],
 'agriculture.rural_development': [('pm_kisan', 'PM-KISAN', 'policy_scheme'),
                                   ('rural_livelihoods', 'Rural Livelihood Programmes', 'policy_scheme'),
                                   ('agri_markets', 'Agricultural Markets (APMC Reforms)', 'process'),
                                   ('overview', 'Rural Development — Overview', 'definition')],
 'agriculture.subsidies_food': [('food_corporation', 'Food Corporation of India', 'institution'),
                                ('pds', 'Public Distribution System', 'policy_scheme'),
                                ('fertilizer_subsidy', 'Fertilizer Subsidy', 'policy_scheme'),
                                ('overview', 'Subsidies and Food Security — Overview', 'definition')],
 'art_culture.architecture': [('overview', 'Indian Architecture — Overview', 'definition'),
                              ('temple_architecture', 'Temple Architecture Styles', 'definition'),
                              ('indo_islamic', 'Indo-Islamic Architecture', 'definition'),
                              ('buddhist_architecture', 'Buddhist Architecture', 'definition'),
                              ('colonial_architecture', 'Colonial Architecture', 'definition'),
                              ('unesco_sites', 'UNESCO World Heritage Sites', 'institution'),
                              ('rock_cut_caves', 'Rock-Cut Cave Architecture', 'definition')],
 'art_culture.heritage_conservation': [('overview', 'Heritage Conservation — Overview', 'definition'),
                                       ('asimap', 'ASI and Heritage Protection', 'institution'),
                                       ('intangible_heritage', 'Intangible Cultural Heritage', 'definition'),
                                       ('conservation_policies', 'Heritage Conservation Policies', 'policy_scheme'),
                                       ('museum_archives', 'Museums and Archives', 'institution'),
                                       ('craft_traditions', 'Traditional Crafts and GI Tags', 'definition')],
 'art_culture.literature': [('overview', 'Indian Literature — Overview', 'definition'),
                            ('sanskrit_literature', 'Sanskrit Literature', 'definition'),
                            ('regional_literature', 'Regional Language Literature', 'definition'),
                            ('philosophy_schools', 'Indian Philosophical Schools', 'definition'),
                            ('modern_literature', 'Modern Indian Literature', 'definition')],
 'art_culture.performing_arts': [('overview', 'Performing Arts — Overview', 'definition'),
                                 ('classical_dance', 'Classical Dance Forms', 'definition'),
                                 ('classical_music', 'Classical Music Traditions', 'definition'),
                                 ('theatre', 'Indian Theatre Traditions', 'definition'),
                                 ('folk_performing', 'Folk Performing Arts', 'definition'),
                                 ('festivals', 'Cultural Festivals', 'event')],
 'art_culture.sculpture_painting': [('overview', 'Sculpture and Painting — Overview', 'definition'),
                                    ('ancient_sculpture', 'Ancient Indian Sculpture', 'definition'),
                                    ('miniature_painting', 'Miniature Painting Schools', 'definition'),
                                    ('modern_art', 'Modern Indian Art', 'definition'),
                                    ('tribal_art', 'Tribal and Folk Art', 'definition'),
                                    ('iconography', 'Iconography and Symbolism', 'definition')],
 'csat.comprehension': [('passage_inference', 'Passage Inference', 'skill'),
                        ('tone_attitude', 'Tone and Attitude Analysis', 'skill'),
                        ('main_idea', 'Main Idea and Summary', 'skill'),
                        ('critical_reading', 'Critical Reading Skills', 'skill'),
                        ('overview', 'Comprehension — Overview', 'skill'),
                        ('fact_opinion', 'Fact vs Opinion Detection', 'skill'),
                        ('vocabulary_context', 'Vocabulary in Context', 'skill'),
                        ('paragraph_structure', 'Paragraph Structure Analysis', 'skill')],
 'csat.decision_making': [('ethical_decisions', 'Ethical Decision Making', 'skill'),
                          ('administrative_situations', 'Administrative Situations', 'skill'),
                          ('interpersonal_conflicts', 'Interpersonal Conflict Resolution', 'skill'),
                          ('public_policy_decisions', 'Public Policy Decision Scenarios', 'skill'),
                          ('overview', 'Decision Making — Overview', 'skill'),
                          ('crisis_response', 'Crisis Response Scenarios', 'skill'),
                          ('resource_allocation', 'Resource Allocation Decisions', 'skill'),
                          ('integrity_scenarios', 'Integrity and Probity Scenarios', 'skill')],
 'csat.logical_reasoning': [('syllogisms', 'Syllogisms and Deduction', 'skill'),
                            ('seating_arrangement', 'Seating Arrangement', 'skill'),
                            ('blood_relations', 'Blood Relations', 'skill'),
                            ('puzzles', 'Logical Puzzles', 'skill'),
                            ('overview', 'Logical Reasoning — Overview', 'skill'),
                            ('statement_assumption', 'Statement and Assumption', 'skill'),
                            ('course_of_action', 'Course of Action', 'skill'),
                            ('direction_sense', 'Direction Sense', 'skill')],
 'csat.quantitative_aptitude': [('percentages', 'Percentages and Ratios', 'skill'),
                                ('time_speed_distance', 'Time, Speed and Distance', 'skill'),
                                ('data_interpretation', 'Data Interpretation', 'skill'),
                                ('number_system', 'Number System', 'skill'),
                                ('overview', 'Quantitative Aptitude — Overview', 'skill'),
                                ('profit_loss', 'Profit and Loss', 'skill'),
                                ('simple_compound_interest', 'Simple and Compound Interest', 'skill'),
                                ('averages', 'Averages and Mixtures', 'skill')],
 'current_affairs.economy': [('rbi_policy_updates', 'RBI Policy Updates', 'meta_current_affairs'),
                             ('budget_highlights', 'Budget and Economic Survey Highlights', 'meta_current_affairs'),
                             ('trade_updates', 'Trade and Investment Updates', 'meta_current_affairs'),
                             ('startup_ecosystem', 'Startup and Innovation Ecosystem', 'meta_current_affairs'),
                             ('overview', 'Economic Affairs — Overview', 'meta_current_affairs'),
                             ('inflation_updates', 'Inflation and Price Trend Updates', 'meta_current_affairs'),
                             ('industrial_policy', 'Industrial Policy Announcements', 'meta_current_affairs'),
                             ('employment_data', 'Employment and Labour Data Releases', 'meta_current_affairs')],
 'current_affairs.international': [('diplomatic_visits', 'Diplomatic Visits and Summits', 'meta_current_affairs'),
                                   ('bilateral_agreements', 'Recent Bilateral Agreements', 'meta_current_affairs'),
                                   ('global_conflicts', 'Global Conflicts Updates', 'meta_current_affairs'),
                                   ('un_reforms', 'UN and Multilateral Updates', 'meta_current_affairs'),
                                   ('overview', 'International Affairs — Overview', 'meta_current_affairs'),
                                   ('trade_agreements', 'Trade Agreement Updates', 'meta_current_affairs'),
                                   ('sanctions_geopolitics',
                                    'Sanctions and Geopolitical Shifts',
                                    'meta_current_affairs'),
                                   ('climate_diplomacy', 'Climate Diplomacy Updates', 'meta_current_affairs')],
 'current_affairs.national': [('government_schemes', 'Recent Government Schemes', 'meta_current_affairs'),
                              ('constitutional_developments',
                               'Constitutional and Legal Developments',
                               'meta_current_affairs'),
                              ('political_developments', 'Political Developments', 'meta_current_affairs'),
                              ('social_issues', 'Contemporary Social Issues', 'meta_current_affairs'),
                              ('overview', 'National Affairs — Overview', 'meta_current_affairs'),
                              ('infrastructure_projects', 'Major Infrastructure Projects', 'meta_current_affairs'),
                              ('state_reforms', 'State-Level Policy Reforms', 'meta_current_affairs'),
                              ('disaster_events', 'Recent Disaster Response Events', 'meta_current_affairs')],
 'current_affairs.polity_governance': [('judicial_verdicts', 'Important Judicial Verdicts', 'meta_current_affairs'),
                                       ('legislative_bills', 'Recent Legislative Bills', 'meta_current_affairs'),
                                       ('governance_reforms', 'Governance Reforms', 'meta_current_affairs'),
                                       ('election_updates',
                                        'Election and Political Process Updates',
                                        'meta_current_affairs'),
                                       ('overview', 'Polity and Governance Affairs — Overview', 'meta_current_affairs'),
                                       ('commission_reports',
                                        'Commission and Committee Reports',
                                        'meta_current_affairs'),
                                       ('administrative_orders',
                                        'Administrative Orders and Notifications',
                                        'meta_current_affairs'),
                                       ('electoral_reforms', 'Electoral Reform Updates', 'meta_current_affairs')],
 'current_affairs.reports_indices': [('economic_survey', 'Economic Survey Key Findings', 'meta_current_affairs'),
                                     ('global_indices', 'Global Indices and Rankings', 'meta_current_affairs'),
                                     ('international_reports',
                                      'International Organization Reports',
                                      'meta_current_affairs'),
                                     ('summits_outcomes', 'Summit Outcomes and Declarations', 'meta_current_affairs'),
                                     ('overview', 'Reports and Indices — Overview', 'meta_current_affairs')],
 'current_affairs.science_env': [('space_missions', 'Recent Space Missions', 'meta_current_affairs'),
                                 ('tech_launches', 'Technology Launches and Breakthroughs', 'meta_current_affairs'),
                                 ('environment_events', 'Environment and Climate Events', 'meta_current_affairs'),
                                 ('health_science', 'Health and Science Updates', 'meta_current_affairs'),
                                 ('overview', 'Science and Environment Affairs — Overview', 'meta_current_affairs')],
 'disaster_management.framework': [('dm_act_2005', 'Disaster Management Act 2005', 'policy_scheme'),
                                   ('sendai_framework', 'Sendai Framework', 'policy_scheme'),
                                   ('disaster_cycle', 'Disaster Management Cycle', 'process'),
                                   ('overview', 'Disaster Management Framework — Overview', 'definition')],
 'disaster_management.institutions': [('ndma', 'National Disaster Management Authority', 'institution'),
                                      ('ndrf', 'National Disaster Response Force', 'institution'),
                                      ('state_dm_authorities', 'State Disaster Management Authorities', 'institution'),
                                      ('overview', 'Disaster Institutions — Overview', 'definition')],
 'disaster_management.types_mitigation': [('earthquakes', 'Earthquake Preparedness', 'process'),
                                          ('floods_cyclones', 'Floods and Cyclones', 'event'),
                                          ('landslides_droughts', 'Landslides and Droughts', 'event'),
                                          ('overview', 'Disaster Types — Overview', 'definition')],
 'economy.agriculture_economics': [('crop_insurance', 'Crop Insurance Schemes', 'policy_scheme'),
                                   ('msp', 'Minimum Support Price', 'policy_scheme'),
                                   ('agri_credit', 'Agricultural Credit', 'process'),
                                   ('land_reforms', 'Land Reforms', 'policy_scheme')],
 'economy.banking': [('commercial_banks', 'Commercial Banking System', 'institution'),
                     ('npas', 'Non-Performing Assets', 'definition'),
                     ('basel_norms', 'Basel Norms', 'policy_scheme'),
                     ('payment_systems', 'Digital Payment Systems', 'process'),
                     ('nbfc', 'NBFCs and Shadow Banking', 'institution'),
                     ('overview', 'Banking — Overview', 'definition'),
                     ('rbi_functions', 'RBI Functions and Monetary Tools', 'institution'),
                     ('cooperative_banks', 'Cooperative and Regional Rural Banks', 'institution')],
 'economy.budget': [('budget_process', 'Union Budget Process', 'process'),
                    ('finance_bill', 'Finance Bill and Appropriation Bill', 'process'),
                    ('gst', 'Goods and Services Tax', 'policy_scheme'),
                    ('direct_indirect_tax', 'Direct and Indirect Taxation', 'definition'),
                    ('overview', 'Budget and Taxation — Overview', 'definition'),
                    ('deficit_types', 'Types of Budget Deficits', 'definition'),
                    ('tax_exemptions', 'Tax Exemptions and Deductions', 'definition'),
                    ('budget_classification', 'Budget Classification', 'definition')],
 'economy.external_sector': [('balance_of_payments', 'Balance of Payments', 'definition'),
                             ('forex_reserves', 'Foreign Exchange Reserves', 'definition'),
                             ('exchange_rate', 'Exchange Rate Regimes', 'definition'),
                             ('fdi_fpi', 'FDI and FPI', 'definition')],
 'economy.fiscal_policy': [('fiscal_deficit', 'Fiscal Deficit', 'definition'),
                           ('primary_deficit', 'Primary Deficit', 'definition'),
                           ('frbm', 'FRBM Act', 'policy_scheme'),
                           ('capital_revenue_expenditure', 'Capital and Revenue Expenditure', 'definition'),
                           ('overview', 'Fiscal Policy — Overview', 'definition'),
                           ('revenue_deficit', 'Revenue Deficit', 'definition'),
                           ('effective_capital', 'Effective Capital Expenditure', 'definition'),
                           ('off_budget_borrowing', 'Off-Budget Borrowing', 'process')],
 'economy.inclusive_growth': [('employment_challenges', 'Employment Challenges', 'definition'),
                              ('skill_development', 'Skill Development Initiatives', 'policy_scheme'),
                              ('financial_inclusion', 'Financial Inclusion', 'policy_scheme')],
 'economy.industry_services': [('manufacturing_sector', 'Manufacturing Sector', 'definition'),
                               ('services_sector', 'Services Sector', 'definition'),
                               ('msme', 'MSME Sector', 'institution')],
 'economy.inflation': [('cpi_wpi', 'CPI and WPI', 'definition'),
                       ('demand_pull_cost_push', 'Demand-Pull and Cost-Push Inflation', 'process'),
                       ('core_inflation', 'Core Inflation', 'definition'),
                       ('phillips_curve', 'Phillips Curve', 'definition'),
                       ('overview', 'Inflation — Overview', 'definition'),
                       ('headline_vs_core', 'Headline vs Core Inflation', 'definition'),
                       ('inflation_targeting', 'Inflation Targeting Framework', 'policy_scheme'),
                       ('wpi_categories', 'WPI Basket Categories', 'definition')],
 'economy.international_economics': [('wto', 'WTO and Trade Agreements', 'institution'),
                                     ('trade_blocs', 'Regional Trade Blocs', 'institution'),
                                     ('overview', 'International Economics — Overview', 'definition')],
 'economy.monetary_policy': [('repo_reverse_repo', 'Repo and Reverse Repo Rate', 'definition'),
                             ('crr_slr', 'CRR and SLR', 'definition'),
                             ('mpc', 'Monetary Policy Committee', 'institution'),
                             ('transmission_mechanism', 'Monetary Transmission Mechanism', 'process'),
                             ('quantitative_easing', 'Quantitative Easing and Liquidity', 'process'),
                             ('overview', 'Monetary Policy — Overview', 'definition'),
                             ('open_market_operations', 'Open Market Operations', 'process'),
                             ('standing_deposit_facility', 'Standing Deposit Facility', 'process')],
 'economy.national_income': [('gdp_gnp', 'GDP and GNP', 'definition'),
                             ('gva', 'Gross Value Added', 'definition'),
                             ('growth_measurement', 'Growth Measurement', 'process'),
                             ('human_development_index', 'Human Development Index', 'definition')],
 'economy.planning': [('planning_commission', 'Planning Commission Legacy', 'institution'),
                      ('niti_role', 'NITI Aayog and Planning', 'institution'),
                      ('overview', 'Planning and Development — Overview', 'definition')],
 'environment.biodiversity': [('biodiversity_levels', 'Levels of Biodiversity', 'definition'),
                              ('biodiversity_hotspots', 'Biodiversity Hotspots', 'definition'),
                              ('endemic_species', 'Endemic and Threatened Species', 'definition'),
                              ('invasive_species', 'Invasive Alien Species', 'definition'),
                              ('biodiversity_act', 'Biological Diversity Act 2002', 'policy_scheme'),
                              ('overview', 'Biodiversity — Overview', 'definition'),
                              ('iucn_red_list', 'IUCN Red List Categories', 'definition'),
                              ('wildlife_protection_act', 'Wildlife Protection Act 1972', 'policy_scheme')],
 'environment.climate_change': [('greenhouse_gases', 'Greenhouse Gases and Global Warming', 'process'),
                                ('ipcc', 'IPCC and Climate Science', 'institution'),
                                ('paris_agreement', 'Paris Agreement', 'policy_scheme'),
                                ('carbon_markets', 'Carbon Markets and Offsets', 'process'),
                                ('climate_impacts_india', 'Climate Change Impacts on India', 'definition'),
                                ('overview', 'Climate Change — Overview', 'definition'),
                                ('net_zero', 'Net Zero Targets', 'policy_scheme'),
                                ('climate_finance', 'Climate Finance Mechanisms', 'process')],
 'environment.conservation': [('protected_areas', 'Protected Area Network', 'institution'),
                              ('project_tiger', 'Project Tiger and Elephant', 'policy_scheme'),
                              ('wetlands', 'Ramsar Wetlands', 'institution'),
                              ('community_conservation', 'Community-Based Conservation', 'process'),
                              ('overview', 'Conservation — Overview', 'definition'),
                              ('biosphere_reserves', 'Biosphere Reserves', 'institution'),
                              ('wildlife_corridors', 'Wildlife Corridors', 'process'),
                              ('ecotourism', 'Ecotourism and Community Reserves', 'process')],
 'environment.ecology_basics': [('ecosystems', 'Ecosystem Structure and Function', 'definition'),
                                ('food_chains', 'Food Chains and Webs', 'process'),
                                ('energy_flow', 'Energy Flow in Ecosystems', 'process'),
                                ('ecological_succession', 'Ecological Succession', 'process'),
                                ('overview', 'Ecology Basics — Overview', 'definition'),
                                ('biomes', 'Major Biomes of the World', 'definition'),
                                ('nutrient_cycles', 'Nutrient Cycles', 'process'),
                                ('ecological_pyramid', 'Ecological Pyramids', 'definition')],
 'environment.environmental_laws': [('epa_1986', 'Environment Protection Act 1986', 'policy_scheme'),
                                    ('forest_wildlife_acts', 'Forest and Wildlife Protection Acts', 'policy_scheme'),
                                    ('ngt', 'National Green Tribunal', 'institution'),
                                    ('moefcc', 'MoEFCC and CPCB/SPCB', 'institution')],
 'environment.pollution': [('air_pollution', 'Air Pollution', 'definition'),
                           ('water_pollution', 'Water Pollution', 'definition'),
                           ('plastic_waste', 'Plastic and Solid Waste', 'definition'),
                           ('e_waste', 'E-Waste Management', 'process'),
                           ('overview', 'Pollution and Waste — Overview', 'definition'),
                           ('smog', 'Smog and Atmospheric Pollution', 'definition'),
                           ('noise_pollution', 'Noise Pollution Standards', 'definition'),
                           ('water_quality', 'Water Quality Standards', 'definition')],
 'environment.sustainable_development': [('sdgs', 'Sustainable Development Goals', 'policy_scheme'),
                                         ('renewable_energy', 'Renewable Energy Transition', 'process'),
                                         ('circular_economy', 'Circular Economy', 'process'),
                                         ('overview', 'Sustainable Development — Overview', 'definition')],
 'essay.economy_environment': [('sustainable_growth', 'Sustainable Growth Essays', 'skill'),
                               ('climate_essays', 'Climate and Environment Essays', 'skill'),
                               ('overview', 'Economy and Environment Essays — Overview', 'skill')],
 'essay.ethics_humanity': [('human_values', 'Human Values Essays', 'skill'),
                           ('compassion_essays', 'Compassion and Humanity Essays', 'skill'),
                           ('overview', 'Ethics and Humanity Essays — Overview', 'skill')],
 'essay.philosophical': [('essay_structure', 'Essay Structure and Flow', 'skill'),
                         ('philosophical_themes', 'Philosophical Essay Themes', 'skill'),
                         ('overview', 'Philosophical Essays — Overview', 'skill')],
 'essay.polity_governance': [('democracy_governance', 'Democracy and Governance Essays', 'skill'),
                             ('federalism_essays', 'Federalism and Decentralization Essays', 'skill'),
                             ('overview', 'Polity and Governance Essays — Overview', 'skill')],
 'essay.society_development': [('development_narratives', 'Development Narratives', 'skill'),
                               ('social_change', 'Social Change Essays', 'skill'),
                               ('overview', 'Society and Development Essays — Overview', 'skill')],
 'ethics.attitude': [('attitude_formation', 'Attitude Formation and Change', 'process'),
                     ('prejudice_stereotypes', 'Prejudice and Stereotypes', 'definition'),
                     ('overview', 'Attitude — Overview', 'definition')],
 'ethics.case_studies': [('ethical_dilemmas', 'Ethical Dilemmas in Administration', 'case_study'),
                         ('crisis_management', 'Crisis Management Ethics', 'case_study'),
                         ('stakeholder_analysis', 'Stakeholder Analysis in Ethics', 'skill'),
                         ('overview', 'Ethics Case Studies — Overview', 'definition')],
 'ethics.emotional_intelligence': [('self_awareness', 'Self-Awareness and Self-Regulation', 'skill'),
                                   ('empathy', 'Empathy and Social Skills', 'skill'),
                                   ('motivation', 'Motivation and Leadership', 'skill'),
                                   ('overview', 'Emotional Intelligence — Overview', 'definition')],
 'ethics.integrity_aptitude': [('integrity', 'Integrity in Public Life', 'definition'),
                               ('honesty', 'Honesty and Impartiality', 'definition'),
                               ('objectivity', 'Objectivity and Dedication', 'definition'),
                               ('overview', 'Integrity and Aptitude — Overview', 'definition')],
 'ethics.probity_governance': [('corruption', 'Corruption and Its Forms', 'definition'),
                               ('code_of_conduct', 'Code of Conduct for Civil Servants', 'policy_scheme'),
                               ('conflict_of_interest', 'Conflict of Interest', 'definition'),
                               ('overview', 'Probity in Governance — Overview', 'definition')],
 'ethics.public_service_values': [('constitutional_values', 'Constitutional Values in Governance', 'definition'),
                                  ('compassion', 'Compassion and Tolerance', 'definition'),
                                  ('commitment', 'Commitment to Public Service', 'definition'),
                                  ('overview', 'Public Service Values — Overview', 'definition')],
 'ethics.theories': [('utilitarianism', 'Utilitarianism', 'definition'),
                     ('deontology', 'Deontological Ethics', 'definition'),
                     ('virtue_ethics', 'Virtue Ethics', 'definition'),
                     ('overview', 'Ethical Theories — Overview', 'definition')],
 'geography.climatology': [('overview', 'Climatology — Overview', 'definition'),
                           ('atmospheric_circulation', 'Atmospheric Circulation', 'process'),
                           ('climate_types', 'Köppen Climate Classification', 'definition'),
                           ('el_nino', 'El Niño and La Niña', 'process'),
                           ('jet_streams', 'Jet Streams and Weather Systems', 'process'),
                           ('greenhouse_effect', 'Greenhouse Effect Basics', 'process')],
 'geography.geomorphology': [('overview', 'Geomorphology — Overview', 'definition'),
                             ('weathering_erosion', 'Weathering and Erosion', 'process'),
                             ('fluvial_landforms', 'Fluvial Landforms', 'definition'),
                             ('glacial_landforms', 'Glacial Landforms', 'definition'),
                             ('coastal_processes', 'Coastal Geomorphic Processes', 'process')],
 'geography.human_economic': [('overview', 'Human and Economic Geography — Overview', 'definition'),
                              ('urbanization', 'Urbanization Patterns', 'definition'),
                              ('migration', 'Migration and Demographic Transition', 'process'),
                              ('industrial_location', 'Industrial Location Factors', 'process'),
                              ('trade_routes', 'Global Trade Routes', 'definition'),
                              ('economic_regions', 'Economic Regions of the World', 'definition')],
 'geography.indian_geography': [('overview', 'Indian Geography — Overview', 'definition'),
                                ('physiographic_divisions', 'Physiographic Divisions of India', 'definition'),
                                ('river_systems', 'Indian River Systems', 'definition'),
                                ('monsoon', 'Indian Monsoon Mechanism', 'process'),
                                ('forests_wildlife', 'Forests and Wildlife', 'definition'),
                                ('agricultural_regions', 'Agricultural Regions', 'definition'),
                                ('transport_network', 'Transport and Communication Networks', 'definition'),
                                ('population_distribution', 'Population Distribution in India', 'definition'),
                                ('coastal_regions', 'Coastal and Island Geography', 'definition')],
 'geography.oceanography': [('overview', 'Oceanography — Overview', 'definition'),
                            ('ocean_currents', 'Ocean Currents', 'process'),
                            ('tides_waves', 'Tides and Waves', 'process'),
                            ('marine_ecosystems', 'Marine Ecosystems', 'definition')],
 'geography.physical': [('overview', 'Physical Geography — Overview', 'definition'),
                        ('earth_structure', 'Earth Structure and Plate Tectonics', 'definition'),
                        ('landforms', 'Major Landform Types', 'definition'),
                        ('soils', 'Soil Types and Distribution', 'definition'),
                        ('natural_vegetation', 'Natural Vegetation', 'definition'),
                        ('earthquakes_volcanoes', 'Earthquakes and Volcanoes', 'event'),
                        ('minerals', 'Mineral Distribution', 'definition'),
                        ('interior_earth', 'Earth Interior and Isostasy', 'definition')],
 'geography.resources': [('overview', 'Resources and Industries — Overview', 'definition'),
                         ('mineral_resources', 'Mineral Resources of India', 'definition'),
                         ('energy_resources', 'Energy Resources', 'definition'),
                         ('industrial_corridors', 'Industrial Corridors and Clusters', 'definition')],
 'geography.world_geography': [('overview', 'World Geography — Overview', 'definition'),
                               ('continents_regions', 'Continents and Major Regions', 'definition'),
                               ('major_rivers', 'Major World River Systems', 'definition'),
                               ('mountain_ranges', 'Major Mountain Ranges', 'definition'),
                               ('deserts_plateaus', 'Deserts and Plateaus', 'definition'),
                               ('strategic_locations', 'Strategic Geographical Locations', 'definition')],
 'governance.citizen_charters': [('rti_act', 'Right to Information Act', 'policy_scheme'),
                                 ('citizen_charter', 'Citizen Charters', 'policy_scheme'),
                                 ('grievance_redressal', 'Grievance Redressal Systems', 'process'),
                                 ('overview', 'Citizen Charters and RTI — Overview', 'definition')],
 'governance.civil_services': [('lateral_entry', 'Lateral Entry Reforms', 'policy_scheme'),
                               ('capacity_building', 'Capacity Building Commission', 'institution'),
                               ('administrative_reforms', 'Administrative Reforms', 'process'),
                               ('overview', 'Civil Services — Overview', 'definition')],
 'governance.e_governance': [('digital_governance', 'Digital Governance Platforms', 'process'),
                             ('umang', 'UMANG and Service Delivery', 'policy_scheme'),
                             ('aadhaar_governance', 'Aadhaar in Governance', 'process'),
                             ('overview', 'E-Governance — Overview', 'definition')],
 'governance.public_policy': [('policy_cycle', 'Public Policy Cycle', 'process'),
                              ('nudge_theory', 'Behavioural Insights and Nudge', 'definition'),
                              ('policy_evaluation', 'Policy Evaluation Methods', 'process'),
                              ('overview', 'Public Policy — Overview', 'definition')],
 'governance.transparency_accountability': [('lokpal', 'Lokpal and Lokayukta', 'institution'),
                                            ('whistleblower', 'Whistleblower Protection', 'policy_scheme'),
                                            ('social_audit', 'Social Audit Mechanisms', 'process'),
                                            ('overview', 'Transparency and Accountability — Overview', 'definition')],
 'history.ancient': [('overview', 'Ancient India — Overview', 'definition'),
                     ('indus_valley', 'Indus Valley Civilization', 'event'),
                     ('vedic_period', 'Vedic Period', 'event'),
                     ('mauryan_empire', 'Mauryan Empire', 'event'),
                     ('gupta_period', 'Gupta Period', 'event'),
                     ('buddhism_jainism', 'Buddhism and Jainism', 'definition'),
                     ('ancient_south_india', 'Ancient South Indian Kingdoms', 'event')],
 'history.freedom_struggle': [('overview', 'Freedom Struggle — Overview', 'definition'),
                              ('non_cooperation', 'Non-Cooperation Movement', 'event'),
                              ('civil_disobedience', 'Civil Disobedience Movement', 'event'),
                              ('quit_india', 'Quit India Movement', 'event'),
                              ('revolutionary_movement', 'Revolutionary Movement', 'event'),
                              ('subhash_chandra_bose', 'Subhash Chandra Bose and INA', 'event'),
                              ('gandhi_programmes', 'Gandhi and Constructive Programmes', 'event'),
                              ('peasant_tribal_movements', 'Peasant and Tribal Movements', 'event'),
                              ('constitutional_development', 'Constitutional Development under British', 'process'),
                              ('cabinet_mission', 'Cabinet Mission and Independence Process', 'event')],
 'history.medieval': [('overview', 'Medieval India — Overview', 'definition'),
                      ('delhi_sultanate', 'Delhi Sultanate', 'event'),
                      ('mughal_administration', 'Mughal Administration', 'process'),
                      ('bhakti_sufi', 'Bhakti and Sufi Movements', 'event'),
                      ('vijayanagara_bahmani', 'Vijayanagara and Bahmani Kingdoms', 'event'),
                      ('mughal_culture', 'Mughal Art and Culture', 'definition')],
 'history.modern': [('overview', 'Modern India — Overview', 'definition'),
                    ('revolt_1857', 'Revolt of 1857', 'event'),
                    ('socio_religious_reforms', 'Socio-Religious Reform Movements', 'event'),
                    ('early_nationalists', 'Early Nationalists (Moderates)', 'event'),
                    ('partition_bengal', 'Partition of Bengal and Swadeshi', 'event'),
                    ('swadeshi', 'Swadeshi Movement', 'event'),
                    ('inc_formation', 'Formation of Indian National Congress', 'event'),
                    ('british_land_revenue', 'British Land Revenue Systems', 'process'),
                    ('press_education', 'British Education and Press Policies', 'process'),
                    ('lahore_session', 'Lahore Session and Poorna Swaraj', 'event')],
 'history.post_independence': [('overview', 'Post-Independence India — Overview', 'definition'),
                               ('integration_princely_states', 'Integration of Princely States', 'event'),
                               ('planning_era', 'Planning Era and Five Year Plans', 'policy_scheme'),
                               ('liberalization_1991', 'Economic Liberalization 1991', 'event'),
                               ('linguistic_reorganization', 'Linguistic Reorganization of States', 'event'),
                               ('wars_conflicts', 'India-Pakistan and China Wars', 'event')],
 'history.world_history': [('overview', 'World History — Overview', 'definition'),
                           ('french_revolution', 'French Revolution', 'event'),
                           ('industrial_revolution', 'Industrial Revolution', 'event'),
                           ('world_wars', 'World Wars I and II', 'event'),
                           ('cold_war', 'Cold War and Bipolar World', 'event'),
                           ('decolonization', 'Decolonization in Asia and Africa', 'event')],
 'internal_security.border_management': [('border_disputes', 'Border Disputes', 'event'),
                                         ('border_infrastructure', 'Border Infrastructure', 'process'),
                                         ('coastal_security', 'Coastal Security', 'process'),
                                         ('overview', 'Border Management — Overview', 'definition')],
 'internal_security.cyber_security': [('cyber_threats', 'Cyber Threat Landscape', 'definition'),
                                      ('cert_in', 'CERT-In and Cyber Framework', 'institution'),
                                      ('critical_infrastructure', 'Critical Information Infrastructure', 'institution'),
                                      ('overview', 'Cyber Security — Overview', 'definition')],
 'internal_security.extremism': [('naxalism', 'Left-Wing Extremism (Naxalism)', 'event'),
                                 ('counter_insurgency', 'Counter-Insurgency Strategy', 'process'),
                                 ('development_security', 'Development-Security Nexus', 'definition'),
                                 ('overview', 'Extremism — Overview', 'definition')],
 'internal_security.organized_crime': [('money_laundering', 'Money Laundering (PMLA)', 'process'),
                                       ('human_trafficking', 'Human Trafficking', 'event'),
                                       ('drug_trafficking', 'Drug Trafficking', 'event'),
                                       ('overview', 'Organized Crime — Overview', 'definition')],
 'internal_security.security_forces': [('army_role', 'Indian Army Internal Security Role', 'institution'),
                                       ('capf', 'Central Armed Police Forces', 'institution'),
                                       ('intelligence_agencies', 'Intelligence Agencies', 'institution'),
                                       ('nsg', 'National Security Guard', 'institution'),
                                       ('overview', 'Security Forces — Overview', 'definition')],
 'internal_security.terrorism': [('terror_organizations', 'Terror Organizations', 'institution'),
                                 ('radicalization', 'Radicalization and De-radicalization', 'process'),
                                 ('counter_terror_laws', 'Counter-Terror Laws (UAPA)', 'policy_scheme'),
                                 ('overview', 'Terrorism — Overview', 'definition')],
 'international_relations.bilateral': [('india_us', 'India-US Relations', 'event'),
                                       ('india_china', 'India-China Relations', 'event'),
                                       ('india_russia', 'India-Russia Relations', 'event'),
                                       ('india_pakistan', 'India-Pakistan Relations', 'event'),
                                       ('overview', 'Bilateral Relations — Overview', 'definition')],
 'international_relations.conflicts': [('ukraine_conflict', 'Ukraine Conflict and Global Impact', 'event'),
                                       ('middle_east', 'Middle East Geopolitics', 'event'),
                                       ('indo_pacific_tensions', 'Indo-Pacific Security Tensions', 'event'),
                                       ('terrorism_global', 'Global Terrorism Networks', 'event'),
                                       ('overview', 'Conflicts and Geopolitics — Overview', 'definition')],
 'international_relations.global_institutions': [('un_system', 'United Nations System', 'institution'),
                                                 ('imf_world_bank', 'IMF and World Bank', 'institution'),
                                                 ('wto_ir', 'WTO in Global Governance', 'institution'),
                                                 ('g20', 'G20', 'institution'),
                                                 ('overview', 'Global Institutions — Overview', 'definition')],
 'international_relations.india_foreign_policy': [('non_alignment',
                                                   'Non-Alignment and Strategic Autonomy',
                                                   'definition'),
                                                  ('neighbourhood_first',
                                                   'Neighbourhood First Policy',
                                                   'policy_scheme'),
                                                  ('act_east', 'Act East Policy', 'policy_scheme'),
                                                  ('indo_pacific', 'Indo-Pacific Strategy', 'policy_scheme'),
                                                  ('overview', 'India Foreign Policy — Overview', 'definition')],
 'international_relations.regional': [('saarc', 'SAARC', 'institution'),
                                      ('asean', 'ASEAN and East Asia Summit', 'institution'),
                                      ('brics', 'BRICS', 'institution'),
                                      ('quad', 'QUAD', 'institution'),
                                      ('overview', 'Regional Groupings — Overview', 'definition')],
 'polity.amendments': [('amendment_process', 'Constitutional Amendment Process', 'process'),
                       ('basic_structure', 'Basic Structure Doctrine', 'case_study'),
                       ('landmark_amendments', 'Landmark Constitutional Amendments', 'policy_scheme'),
                       ('overview', 'Amendments — Overview', 'definition')],
 'polity.center_state_relations': [('legislative_relations', 'Legislative Relations', 'process'),
                                   ('administrative_relations', 'Administrative Relations', 'process'),
                                   ('financial_relations', 'Financial Relations', 'process'),
                                   ('overview', 'Centre-State Relations — Overview', 'definition')],
 'polity.constitution_basics': [('making_of_constitution', 'Making of the Constitution', 'process'),
                                ('sources_of_constitution', 'Sources of the Constitution', 'definition'),
                                ('preamble', 'Preamble', 'definition'),
                                ('citizenship', 'Citizenship', 'definition'),
                                ('overview', 'Constitution Basics — Overview', 'definition'),
                                ('salient_features', 'Salient Features of the Constitution', 'definition'),
                                ('schedules', 'Schedules of the Constitution', 'definition'),
                                ('union_territory_provisions', 'Union and Its Territory Provisions', 'definition')],
 'polity.constitutional_bodies': [('cag', 'Comptroller and Auditor General', 'institution'),
                                  ('ec', 'Election Commission', 'institution'),
                                  ('upsc', 'Union Public Service Commission', 'institution'),
                                  ('finance_commission', 'Finance Commission', 'institution'),
                                  ('ncsc_ncst', 'NCSC and NCST', 'institution')],
 'polity.dpsp': [('overview', 'Directive Principles — Overview', 'definition'),
                 ('socialistic_principles', 'Socialistic Principles', 'definition'),
                 ('gandhian_principles', 'Gandhian Principles', 'definition'),
                 ('implementation_dpsp', 'Implementation of DPSP', 'process'),
                 ('conflict_fr_dpsp', 'FR-DPSP Relationship', 'definition')],
 'polity.emergency': [('national_emergency', 'National Emergency (Art. 352)', 'process'),
                      ('state_emergency', 'State Emergency (Art. 356)', 'process'),
                      ('financial_emergency', 'Financial Emergency (Art. 360)', 'process')],
 'polity.federalism': [('federal_features', 'Federal Features of Indian Constitution', 'definition'),
                       ('quasi_federal', 'Quasi-Federal Character', 'definition'),
                       ('interstate_council', 'Inter-State Council', 'institution'),
                       ('interstate_disputes', 'Inter-State Disputes', 'process'),
                       ('overview', 'Federalism — Overview', 'definition'),
                       ('union_list', 'Union, State and Concurrent Lists', 'definition'),
                       ('governor_role', 'Governor in Federal Setup', 'institution'),
                       ('union_territories', 'Union Territories Administration', 'institution')],
 'polity.fundamental_duties': [('overview', 'Fundamental Duties — Overview', 'definition'),
                               ('list_of_duties', 'List of Fundamental Duties', 'definition'),
                               ('enforceability', 'Enforceability of Duties', 'process')],
 'polity.fundamental_rights': [('overview', 'Fundamental Rights — Overview', 'definition', None),
                               ('article_14', 'Article 14 — Equality Before Law', 'definition', 'overview'),
                               ('article_19', 'Article 19 — Six Freedoms', 'definition', 'overview'),
                               ('article_21', 'Article 21 — Life & Liberty', 'definition', 'overview'),
                               ('article_21a', 'Article 21A — Right to Education', 'definition', 'article_21'),
                               ('article_32', 'Article 32 — Constitutional Remedies', 'definition', 'overview'),
                               ('reasonable_restrictions', 'Reasonable Restrictions', 'process', 'overview'),
                               ('writ_jurisdiction', 'Writ Jurisdiction (32 & 226)', 'process', 'overview'),
                               ('habeas_corpus', 'Habeas Corpus', 'definition', 'writ_jurisdiction'),
                               ('mandal_kesavananda',
                                'Landmark Cases (Kesavananda, Maneka, etc.)',
                                'case_study',
                                'overview')],
 'polity.judiciary': [('supreme_court', 'Supreme Court', 'institution'),
                      ('high_courts', 'High Courts', 'institution'),
                      ('judicial_review', 'Judicial Review', 'process'),
                      ('collegium', 'Collegium System', 'institution'),
                      ('tribunals', 'Tribunals and Special Courts', 'institution'),
                      ('judicial_activism', 'Judicial Activism and Overreach', 'process'),
                      ('overview', 'Judiciary — Overview', 'definition'),
                      ('subordinate_judiciary', 'Subordinate Judiciary', 'institution')],
 'polity.local_government': [('panchayati_raj', 'Panchayati Raj Institutions', 'institution'),
                             ('municipalities', 'Urban Local Bodies', 'institution'),
                             ('73rd_74th_amendments', '73rd and 74th Amendments', 'policy_scheme'),
                             ('overview', 'Local Government — Overview', 'definition')],
 'polity.non_constitutional_bodies': [('nhrc', 'National Human Rights Commission', 'institution'),
                                      ('ncw', 'National Commission for Women', 'institution'),
                                      ('ncpcr', 'NCPCR', 'institution'),
                                      ('niti_aayog', 'NITI Aayog', 'institution'),
                                      ('rbi_as_non_constitutional', 'RBI as Statutory Body', 'institution')],
 'polity.parliament': [('structure', 'Parliament — Structure', 'definition'),
                       ('sessions', 'Parliamentary Sessions', 'process'),
                       ('legislative_process', 'Legislative Process', 'process'),
                       ('budget_process', 'Budget Process', 'process'),
                       ('committees', 'Parliamentary Committees', 'institution'),
                       ('privileges', 'Parliamentary Privileges', 'definition'),
                       ('joint_sitting', 'Joint Sitting and Deadlock Resolution', 'process'),
                       ('overview', 'Parliament — Overview', 'definition')],
 'polity.union_executive': [('president', 'President of India', 'institution'),
                            ('vice_president', 'Vice President of India', 'institution'),
                            ('pm_council', 'Prime Minister and Council of Ministers', 'institution'),
                            ('cabinet', 'Cabinet and Cabinet Committees', 'institution'),
                            ('overview', 'Union Executive — Overview', 'definition'),
                            ('ordinances', 'Ordinance Making Power', 'process'),
                            ('pardoning_power', 'Pardoning Power of President', 'process'),
                            ('collective_responsibility', 'Collective Responsibility', 'definition')],
 'science_technology.biotechnology': [('genetic_engineering', 'Genetic Engineering', 'process'),
                                      ('stem_cells', 'Stem Cell Research', 'process'),
                                      ('vaccines', 'Vaccine Technology', 'process'),
                                      ('biopharma', 'Biopharmaceutical Industry', 'institution'),
                                      ('overview', 'Biotechnology — Overview', 'definition')],
 'science_technology.defence': [('missile_systems', 'Missile Systems', 'definition'),
                                ('drone_technology', 'Drone and UAV Technology', 'process'),
                                ('indigenous_defence', 'Indigenous Defence Manufacturing', 'policy_scheme'),
                                ('overview', 'Defence Technology — Overview', 'definition')],
 'science_technology.energy': [('nuclear_energy', 'Nuclear Energy', 'process'),
                               ('solar_wind', 'Solar and Wind Energy', 'process'),
                               ('hydrogen_energy', 'Green Hydrogen', 'process'),
                               ('energy_storage', 'Energy Storage Technologies', 'process'),
                               ('overview', 'Energy Science — Overview', 'definition')],
 'science_technology.general_science': [('physics_mechanics', 'Physics — Mechanics and Optics', 'definition'),
                                        ('chemistry_basics', 'Chemistry — Acids, Bases and Reactions', 'definition'),
                                        ('biology_cell', 'Biology — Cell and Genetics', 'definition'),
                                        ('human_body', 'Human Body Systems', 'definition'),
                                        ('diseases_immunity', 'Diseases and Immunity', 'definition'),
                                        ('nutrition', 'Nutrition and Health', 'definition'),
                                        ('magnetism_electricity', 'Magnetism and Electricity', 'definition'),
                                        ('periodic_table', 'Periodic Table and Elements', 'definition'),
                                        ('photosynthesis', 'Photosynthesis and Respiration', 'definition'),
                                        ('evolution', 'Evolution and Classification', 'definition'),
                                        ('scientific_instruments', 'Scientific Instruments', 'definition'),
                                        ('overview', 'General Science — Overview', 'definition')],
 'science_technology.it_digital': [('digital_india', 'Digital India Initiative', 'policy_scheme'),
                                   ('ai_ml', 'Artificial Intelligence and ML', 'definition'),
                                   ('cybersecurity_tech', 'Cybersecurity Technology', 'process'),
                                   ('blockchain', 'Blockchain and DLT', 'definition'),
                                   ('data_protection', 'Data Protection Framework', 'policy_scheme'),
                                   ('overview', 'IT and Digital Technology — Overview', 'definition'),
                                   ('5g_technology', '5G and Telecom Infrastructure', 'process'),
                                   ('digital_public_infrastructure',
                                    'Digital Public Infrastructure (UPI, ONDC)',
                                    'process')],
 'science_technology.materials_nano': [('nanotechnology', 'Nanotechnology Applications', 'process'),
                                       ('advanced_materials', 'Advanced Materials', 'definition'),
                                       ('semiconductors', 'Semiconductor Technology', 'process')],
 'science_technology.space': [('isro_programmes', 'ISRO Programmes', 'institution'),
                              ('satellite_launch', 'Satellite Launch Vehicles', 'process'),
                              ('planetary_missions', 'Planetary Exploration Missions', 'event'),
                              ('space_applications', 'Space Applications', 'process'),
                              ('overview', 'Space Technology — Overview', 'definition')],
 'social_justice.education_health': [('samagra_shiksha', 'Samagra Shiksha', 'policy_scheme'),
                                     ('nep_2020', 'National Education Policy 2020', 'policy_scheme'),
                                     ('nhm', 'National Health Mission', 'policy_scheme'),
                                     ('nutrition_programmes', 'Nutrition Programmes', 'policy_scheme'),
                                     ('overview', 'Education and Health — Overview', 'definition')],
 'social_justice.poverty_hunger': [('poverty_measurement', 'Poverty Measurement', 'definition'),
                                   ('nfsa', 'National Food Security Act', 'policy_scheme'),
                                   ('mgnrega', 'MGNREGA', 'policy_scheme'),
                                   ('malnutrition', 'Malnutrition and Anaemia', 'definition'),
                                   ('overview', 'Poverty and Hunger — Overview', 'definition')],
 'social_justice.vulnerable_sections': [('sc_st_welfare', 'SC and ST Welfare', 'policy_scheme'),
                                        ('disability_rights', 'Disability Rights', 'policy_scheme'),
                                        ('minority_welfare', 'Minority Welfare', 'policy_scheme'),
                                        ('transgender_rights', 'Transgender Rights', 'policy_scheme'),
                                        ('overview', 'Vulnerable Sections — Overview', 'definition')],
 'social_justice.welfare_schemes': [('pm_jan_dhan', 'PM Jan Dhan Yojana', 'policy_scheme'),
                                    ('pm_awas', 'PM Awas Yojana', 'policy_scheme'),
                                    ('pm_ujjwala', 'PM Ujjwala Yojana', 'policy_scheme'),
                                    ('ayushman_bharat', 'Ayushman Bharat', 'policy_scheme'),
                                    ('overview', 'Welfare Schemes — Overview', 'definition')],
 'society.globalization_society': [('cultural_globalization', 'Cultural Globalization', 'process'),
                                   ('migration_society', 'Migration and Diaspora', 'process'),
                                   ('media_society', 'Media and Society', 'process'),
                                   ('overview', 'Globalization and Society — Overview', 'definition')],
 'society.indian_society_structure': [('caste_system', 'Caste and Social Stratification', 'definition'),
                                      ('tribal_society', 'Tribal Societies', 'definition'),
                                      ('religious_diversity', 'Religious Diversity', 'definition'),
                                      ('overview', 'Indian Society Structure — Overview', 'definition')],
 'society.population_urbanization': [('demographic_dividend', 'Demographic Dividend', 'definition'),
                                     ('urbanization_trends', 'Urbanization Trends', 'definition'),
                                     ('smart_cities', 'Smart Cities Mission', 'policy_scheme'),
                                     ('overview', 'Population and Urbanization — Overview', 'definition')],
 'society.social_movements': [('environmental_movements', 'Environmental Movements', 'event'),
                              ('farmers_movements', 'Farmers Movements', 'event'),
                              ('labour_movements', 'Labour Movements', 'event'),
                              ('overview', 'Social Movements — Overview', 'definition')],
 'society.women_children': [('women_empowerment', 'Women Empowerment', 'definition'),
                            ('child_rights', 'Child Rights and Protection', 'policy_scheme'),
                            ('gender_gap', 'Gender Gap and Equality', 'definition'),
                            ('overview', 'Women and Children — Overview', 'definition')]}

def _subject_id(slug: str) -> str:
    return f"{EXAM_CODE}.{slug}"


def _topic_id(subject_slug: str, topic_slug: str) -> str:
    return f"{EXAM_CODE}.{subject_slug}.{topic_slug}"


def _concept_id(topic_id: str, concept_slug: str) -> str:
    return f"{topic_id}.{concept_slug}"


def _relationship_id(source_id: str, relationship_type: str, target_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{EXAM_ID}:{source_id}:{relationship_type}:{target_id}"))


def _default_ca_linkable(subject_slug: str, concept_type: str) -> bool:
    if subject_slug == "csat":
        return False
    if concept_type == "skill" and subject_slug == "essay":
        return False
    return True


def _default_pyq_mappable(subject_slug: str, concept_type: str) -> bool:
    if subject_slug in {"essay", "csat"}:
        return False
    if concept_type in {"skill", "meta_current_affairs"}:
        return subject_slug != "current_affairs"
    return True


def _concept_relevance(
    *,
    topic_prelims: int,
    topic_mains: int,
    subject_slug: str,
    index: int,
    total: int,
) -> tuple[int, int]:
    if subject_slug == "csat":
        return max(70, topic_prelims - index), 0
    if subject_slug in {"ethics", "essay"}:
        return 0, max(70, topic_mains - index)
    prelims = max(0, min(100, topic_prelims - index)) if topic_prelims > 0 else 0
    mains = max(0, min(100, topic_mains - index)) if topic_mains > 0 else 0
    if total <= 1:
        return prelims, mains
    return prelims, mains


def _build_exam() -> dict[str, object]:
    return {
        "exam_id": EXAM_ID,
        "exam_code": EXAM_CODE,
        "exam_name": "Union Public Service Commission — Civil Services Examination",
        "exam_type": "competitive_civil_services",
        "prelims_weight": "0.25",
        "mains_weight": "0.55",
        "interview_weight": "0.20",
        "domain_catalog_version": CATALOG_VERSION,
        "essay_included": True,
        "status": "active",
    }


def _build_subjects() -> list[dict[str, object]]:
    subjects: list[dict[str, object]] = []
    for index, subject in enumerate(SUBJECTS, start=1):
        subjects.append(
            {
                "subject_id": _subject_id(subject["slug"]),
                "exam_id": EXAM_ID,
                "subject_name": subject["name"],
                "subject_slug": subject["slug"],
                "prelims_applicable": subject["prelims_applicable"],
                "mains_applicable": subject["mains_applicable"],
                "sort_order": index,
                "status": "active",
            }
        )
    return subjects


def _build_topics() -> list[dict[str, object]]:
    topics: list[dict[str, object]] = []
    for subject in SUBJECTS:
        subject_id = _subject_id(subject["slug"])
        for index, topic in enumerate(subject["topics"], start=1):
            topics.append(
                {
                    "topic_id": _topic_id(subject["slug"], topic["slug"]),
                    "exam_id": EXAM_ID,
                    "subject_id": subject_id,
                    "topic_name": topic["name"],
                    "topic_slug": topic["slug"],
                    "prelims_relevance": topic["prelims_relevance"],
                    "mains_relevance": topic["mains_relevance"],
                    "sort_order": index,
                    "status": "active",
                }
            )
    return topics


def _build_tracks() -> list[dict[str, object]]:
    tracks: list[dict[str, object]] = []
    for index, track in enumerate(TRACK_DEFINITIONS, start=1):
        subject_slugs = track["subject_slugs"]
        assert isinstance(subject_slugs, list)
        tracks.append(
            {
                "track_id": f"{EXAM_ID}.{track['track_code']}",
                "exam_id": EXAM_ID,
                "track_code": track["track_code"],
                "track_name": track["track_name"],
                "stage": track["stage"],
                "subject_ids": [_subject_id(str(slug)) for slug in subject_slugs],
                "sort_order": index,
                "status": "active",
            }
        )
    return tracks


def _build_concepts() -> list[dict[str, object]]:
    concepts: list[dict[str, object]] = []
    topic_lookup = {
        _topic_id(subject["slug"], topic["slug"]): (subject["slug"], topic)
        for subject in SUBJECTS
        for topic in subject["topics"]
    }

    for topic_key, specs in CONCEPTS_BY_TOPIC.items():
        subject_slug, topic_slug = topic_key.split(".", 1)
        topic_id = _topic_id(subject_slug, topic_slug)
        subject_id = _subject_id(subject_slug)
        _, topic_spec = topic_lookup[topic_id]
        total = len(specs)

        slug_to_id: dict[str, str] = {}
        for spec in specs:
            slug = spec[0]
            slug_to_id[slug] = _concept_id(topic_id, slug)

        for index, spec in enumerate(specs):
            slug, name, concept_type = spec[0], spec[1], spec[2]
            parent_slug = spec[3] if len(spec) > 3 else None
            prelims, mains = _concept_relevance(
                topic_prelims=topic_spec["prelims_relevance"],
                topic_mains=topic_spec["mains_relevance"],
                subject_slug=subject_slug,
                index=index,
                total=total,
            )
            parent_id = slug_to_id.get(parent_slug) if parent_slug else None
            exam_stages = derive_exam_stages(
                prelims_relevance=prelims,
                mains_relevance=mains,
                subject_slug=subject_slug,
            )
            concepts.append(
                {
                    "concept_id": slug_to_id[slug],
                    "exam_id": EXAM_ID,
                    "subject_id": subject_id,
                    "topic_id": topic_id,
                    "concept_name": name,
                    "concept_slug": slug,
                    "concept_type": concept_type,
                    "prelims_relevance": prelims,
                    "mains_relevance": mains,
                    "parent_concept_id": parent_id,
                    "current_affairs_linkable": _default_ca_linkable(subject_slug, concept_type),
                    "pyq_mappable": _default_pyq_mappable(subject_slug, concept_type),
                    "interview_relevance": 0,
                    "difficulty": 3,
                    "importance": None,
                    "importance_version": None,
                    "pyq_count": 0,
                    "exam_stages": list(exam_stages),
                    "tags": [],
                    "status": "active",
                    "domain_catalog_version": CATALOG_VERSION,
                }
            )
    return concepts


def _build_relationships(concepts: list[dict[str, object]]) -> list[dict[str, object]]:
    concept_ids = {concept["concept_id"] for concept in concepts}

    def cid(topic_suffix: str, concept_slug: str) -> str:
        return f"{EXAM_CODE}.{topic_suffix}.{concept_slug}"

    relationship_specs: list[tuple[str, str, str]] = [
        # Spec §10.4 — Polity
        (cid("polity.fundamental_rights", "article_14"), "PREREQUISITE", cid("polity.fundamental_rights", "overview")),
        (cid("polity.fundamental_rights", "article_19"), "PREREQUISITE", cid("polity.fundamental_rights", "overview")),
        (cid("polity.fundamental_rights", "writ_jurisdiction"), "BUILDS_ON", cid("polity.fundamental_rights", "article_32")),
        (cid("polity.fundamental_rights", "overview"), "RELATED_TO", cid("polity.dpsp", "overview")),
        (cid("polity.parliament", "legislative_process"), "PREREQUISITE", cid("polity.parliament", "structure")),
        (cid("polity.judiciary", "judicial_review"), "BUILDS_ON", cid("polity.fundamental_rights", "overview")),
        # Spec §6.5 — additional Fundamental Rights edges
        (cid("polity.fundamental_rights", "article_21"), "PREREQUISITE", cid("polity.fundamental_rights", "overview")),
        (cid("polity.fundamental_rights", "article_32"), "PREREQUISITE", cid("polity.fundamental_rights", "overview")),
        (cid("polity.fundamental_rights", "habeas_corpus"), "BUILDS_ON", cid("polity.fundamental_rights", "writ_jurisdiction")),
    ]

    relationships: list[dict[str, object]] = []
    for source_id, relationship_type, target_id in relationship_specs:
        if source_id not in concept_ids or target_id not in concept_ids:
            continue
        relationships.append(
            {
                "id": _relationship_id(source_id, relationship_type, target_id),
                "exam_id": EXAM_ID,
                "source_id": source_id,
                "source_type": "concept",
                "target_id": target_id,
                "target_type": "concept",
                "relationship_type": relationship_type,
                "weight": "1.0",
                "status": "active",
            }
        )
    return relationships


def build_catalog_seed() -> dict[str, object]:
    """Build the complete UPSC CSE catalog seed payload."""
    concepts = _build_concepts()
    return {
        "catalog_version": CATALOG_VERSION,
        "exam_id": EXAM_ID,
        "exam": _build_exam(),
        "tracks": _build_tracks(),
        "subjects": _build_subjects(),
        "topics": _build_topics(),
        "concepts": concepts,
        "relationships": _build_relationships(concepts),
    }


def count_active_concepts_by_subject() -> dict[str, int]:
    """Return active concept counts keyed by subject slug."""
    counts: dict[str, int] = {}
    for concept in _build_concepts():
        if concept["status"] != "active":
            continue
        subject_slug = str(concept["subject_id"]).removeprefix(f"{EXAM_CODE}.")
        counts[subject_slug] = counts.get(subject_slug, 0) + 1
    return counts
