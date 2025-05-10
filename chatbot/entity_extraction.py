# entity_extraction.py
# Advanced entity extraction using spaCy

import os
import re
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot.entity_extraction")

# Initialize spaCy if available
try:
    import spacy
    spacy_available = True
    
    # Try to load model
    try:
        # Check if model exists
        if spacy.util.is_package("en_core_web_sm"):
            nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        else:
            logger.warning("spaCy model 'en_core_web_sm' not found. Using blank model.")
            logger.warning("Install the model with: python -m spacy download en_core_web_sm")
            nlp = spacy.blank("en")
            
    except Exception as e:
        logger.error(f"Error loading spaCy model: {e}")
        logger.warning("Using blank model instead")
        nlp = spacy.blank("en")
        
except ImportError:
    logger.warning("spaCy not installed, falling back to regex-based entity extraction")
    logger.warning("Install spaCy with: pip install spacy")
    logger.warning("Then download a model: python -m spacy download en_core_web_sm")
    spacy_available = False
    nlp = None

def extract_entities_regex(text):
    """
    Extract entities using regular expressions (fallback method)
    
    Args:
        text (str): User message
        
    Returns:
        dict: Extracted entities
    """
    entities = {}
    
    # Extract locations (cities, countries)
    location_patterns = [
        # City + state/country pattern
        r'in ([A-Z][a-z]+(?:[ -][A-Z][a-z]+)*),? ([A-Z][a-z]+(?:[ -][A-Z][a-z]+)*)',
        # Single city/location
        r'(?:in|at|from|to) ([A-Z][a-z]+(?:[ -][A-Z][a-z]+)*)',
        # For "New York" type cities with space
        r'(?:in|at|from|to) ([A-Z][a-z]+ [A-Z][a-z]+)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            # Check if pattern has multiple groups
            if len(match.groups()) > 1:
                city = match.group(1)
                region = match.group(2)
                entities['city'] = city
                entities['region'] = region
                entities['location'] = f"{city}, {region}"
            else:
                location = match.group(1)
                entities['location'] = location
            break  # Stop after first match
    
    # Extract dates
    date_patterns = [
        # YYYY-MM-DD format
        r'(\d{4}-\d{2}-\d{2})',
        # MM/DD/YYYY format
        r'(\d{1,2}/\d{1,2}/\d{4})',
        # Month day, year format
        r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})',
        # Day month year format
        r'(\d{1,2})(?:st|nd|rd|th)? (January|February|March|April|May|June|July|August|September|October|November|December),? (\d{4})',
        # Relative dates
        r'(today|tomorrow|yesterday)',
        # Days of week
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.group(1).lower() in ['today', 'tomorrow', 'yesterday']:
                entities['date'] = match.group(1).lower()
            elif match.group(1).title() in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                entities['day_of_week'] = match.group(1).title()
            else:
                # Various date formats
                if len(match.groups()) == 1:
                    entities['date'] = match.group(1)
                elif len(match.groups()) == 3:
                    # Either Month day, year or day month year
                    try:
                        int(match.group(1))
                        # day month year
                        entities['date'] = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    except ValueError:
                        # Month day, year
                        entities['date'] = f"{match.group(1)} {match.group(2)}, {match.group(3)}"
            break  # Stop after first match
    
    # Extract time
    time_patterns = [
        # 24-hour format
        r'(\d{1,2}:\d{2})',
        # 12-hour format with AM/PM
        r'(\d{1,2}(?::\d{2})? [APap][Mm])',
        # Words like "noon", "midnight"
        r'(noon|midnight)'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            entities['time'] = match.group(1)
            break  # Stop after first match
    
    # Extract numbers
    number_patterns = [
        # Extract specific numbers
        r'(\d+(?:\.\d+)?)',
        # Extract numbers written as words (limited)
        r'(one|two|three|four|five|six|seven|eight|nine|ten)'
    ]
    
    # We don't break after first match for numbers, to collect all of them
    for pattern in number_patterns:
        for match in re.finditer(pattern, text.lower()):
            if 'numbers' not in entities:
                entities['numbers'] = []
            
            # Convert word numbers to digits
            value = match.group(1)
            word_to_number = {
                'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
                'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10'
            }
            
            if value in word_to_number:
                value = word_to_number[value]
            
            entities['numbers'].append(value)
    
    # Extract names (basic patterns)
    name_patterns = [
        # "My name is X"
        r'my name is ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)',
        # "I am X"
        r'I am ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)',
        # "I'm X"
        r'I\'m ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)',
        # "Call me X"
        r'call me ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            entities['person_name'] = match.group(1)
            break  # Stop after first match
    
    # Extract email addresses
    email_pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    match = re.search(email_pattern, text)
    if match:
        entities['email'] = match.group(1)
    
    # Extract phone numbers (various formats)
    phone_patterns = [
        # (555) 123-4567
        r'\((\d{3})\) (\d{3})-(\d{4})',
        # 555-123-4567
        r'(\d{3})-(\d{3})-(\d{4})',
        # 5551234567
        r'(\d{10})'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                entities['phone'] = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
            elif len(match.groups()) == 1:
                num = match.group(1)
                if len(num) == 10:
                    entities['phone'] = f"({num[0:3]}) {num[3:6]}-{num[6:10]}"
            break  # Stop after first match
    
    # Extract favorite things
    favorite_pattern = r'(?:favorite|favourites) (color|colour|food|movie|film|book|animal|music|song|place|holiday|hobby) (?:is|are) ([\w\s]+)'
    match = re.search(favorite_pattern, text, re.IGNORECASE)
    if match:
        category = match.group(1).lower()
        # Normalize some categories
        if category == 'colour':
            category = 'color'
        if category == 'film':
            category = 'movie'
        
        value = match.group(2).strip()
        entities[f'favorite_{category}'] = value
    
    return entities

def extract_entities_spacy(text):
    """
    Extract entities using spaCy NLP
    
    Args:
        text (str): User message
        
    Returns:
        dict: Extracted entities
    """
    if not spacy_available or nlp is None:
        logger.warning("spaCy not available, falling back to regex-based extraction")
        return extract_entities_regex(text)
    
    entities = {}
    
    # Process text with spaCy
    doc = nlp(text)
    
    # Extract named entities
    for ent in doc.ents:
        entity_type = ent.label_.lower()
        entity_text = ent.text
        
        # Map spaCy entity types to our categories
        if entity_type in ['gpe', 'loc', 'fac']:
            # Geographical entities, locations, facilities
            if 'location' not in entities:
                entities['location'] = entity_text
        
        elif entity_type == 'person':
            if 'person' not in entities:
                entities['person'] = entity_text
        
        elif entity_type == 'date':
            if 'date' not in entities:
                entities['date'] = entity_text
        
        elif entity_type == 'time':
            if 'time' not in entities:
                entities['time'] = entity_text
        
        elif entity_type in ['cardinal', 'money', 'percent', 'quantity']:
            if 'numbers' not in entities:
                entities['numbers'] = []
            entities['numbers'].append(entity_text)
        
        elif entity_type == 'org':
            if 'organization' not in entities:
                entities['organization'] = entity_text
        
        else:
            # Store other entity types as-is
            if entity_type not in entities:
                entities[entity_type] = entity_text
    
    # Extract additional entities that spaCy might miss
    # Names in specific formats
    name_patterns = [
        r'my name is ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)',
        r'I am ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)',
        r'I\'m ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)',
        r'call me ([A-Z][a-z]+(?:[ \'-][A-Z][a-z]+)*)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and 'person' not in entities:
            entities['person_name'] = match.group(1)
            break
    
    # Extract email and phone which spaCy often misses
    email_pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    match = re.search(email_pattern, text)
    if match:
        entities['email'] = match.group(1)
    
    phone_patterns = [
        r'\((\d{3})\) (\d{3})-(\d{4})',
        r'(\d{3})-(\d{3})-(\d{4})',
        r'(\d{10})'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                entities['phone'] = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
            elif len(match.groups()) == 1:
                num = match.group(1)
                if len(num) == 10:
                    entities['phone'] = f"({num[0:3]}) {num[3:6]}-{num[6:10]}"
            break
    
    # Extract favorite things
    favorite_pattern = r'(?:favorite|favourites) (color|colour|food|movie|film|book|animal|music|song|place|holiday|hobby) (?:is|are) ([\w\s]+)'
    match = re.search(favorite_pattern, text, re.IGNORECASE)
    if match:
        category = match.group(1).lower()
        # Normalize some categories
        if category == 'colour':
            category = 'color'
        if category == 'film':
            category = 'movie'
        
        value = match.group(2).strip()
        entities[f'favorite_{category}'] = value
    
    return entities

def extract_entities(text):
    """
    Extract entities from text, using spaCy if available, falling back to regex
    
    Args:
        text (str): User message
        
    Returns:
        dict: Extracted entities
    """
    if spacy_available and nlp is not None:
        return extract_entities_spacy(text)
    else:
        return extract_entities_regex(text)

if __name__ == "__main__":
    # Test with some example text
    test_texts = [
        "My name is Sarah Johnson and I live in New York",
        "The weather in Los Angeles, California looks great today",
        "I'm going to Paris on January 15, 2026",
        "Call me at (555) 123-4567 or email me at test@example.com",
        "My favorite color is blue and my favorite movie is The Matrix",
        "I need to wake up at 7:30 AM tomorrow for my meeting",
        "The temperature is 25 degrees and humidity is 45 percent"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\nExample {i+1}: \"{text}\"")
        
        # Extract entities
        entities = extract_entities(text)
        
        # Print results
        if entities:
            print("Extracted entities:")
            for key, value in entities.items():
                print(f"  - {key}: {value}")
        else:
            print("No entities extracted")