"""
Habit Normalization Service - Business Logic Layer

Chịu trách nhiệm:
- Normalize app names
- Business logic for name standardization
"""

from typing import Dict


class HabitNormalizationService:
    """Service for normalizing app names and related business logic"""
    
    # App name aliases mapping - normalize different names to canonical form
    APP_ALIASES = {
        # Browsers
        'chrome.exe': 'chrome',
        'google chrome': 'chrome',
        'firefox.exe': 'firefox',
        'mozilla firefox': 'firefox',
        'msedge.exe': 'edge',
        'microsoft edge': 'edge',
        
        # Development
        'vscode.exe': 'vscode',
        'visual studio': 'visual studio',
        'pycharm.exe': 'pycharm',
        'intellij': 'intellij',
        'windsurf.exe': 'windsurf',
        'cursor.exe': 'cursor',
        
        # Communication
        'discord.exe': 'discord',
        'telegram.exe': 'telegram',
        'slack.exe': 'slack',
        'teams.exe': 'teams',
        
        # Gaming
        'steam.exe': 'steam',
        'epic games': 'epic games',
        'valorant.exe': 'valorant',
        'lol.exe': 'lol',
        'fortnite.exe': 'fortnite',
        'minecraft.exe': 'minecraft',
    }
    
    @classmethod
    def normalize_app_name(cls, app_name: str) -> str:
        """Normalize app name using aliases dictionary"""
        if not app_name:
            return app_name
        return cls.APP_ALIASES.get(app_name.lower(), app_name)
    
    @classmethod
    def get_app_category(cls, app_name: str) -> str:
        """Get category for an app based on normalized name"""
        normalized = cls.normalize_app_name(app_name)
        
        categories = {
            'chrome': 'browser',
            'firefox': 'browser', 
            'edge': 'browser',
            'vscode': 'development',
            'pycharm': 'development',
            'intellij': 'development',
            'windsurf': 'development',
            'cursor': 'development',
            'discord': 'communication',
            'telegram': 'communication',
            'slack': 'communication',
            'teams': 'communication',
            'steam': 'gaming',
            'epic games': 'gaming',
            'valorant': 'gaming',
            'lol': 'gaming',
            'fortnite': 'gaming',
            'minecraft': 'gaming',
        }
        
        return categories.get(normalized, 'other')
