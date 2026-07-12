"""Apartment/flat parser from krisha.kz HTML"""

import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from krisha_parser.config.config import Config
from krisha_parser.db.models import Apartment

logger = logging.getLogger()


class FlatParser:
    """Parse apartment listings from krisha.kz HTML"""
    
    BASE_URL = "https://krisha.kz"
    
    def __init__(self, soup: BeautifulSoup, config: Config):
        self.soup = soup
        self.config = config
    
    def parse(self) -> List[Apartment]:
        """Parse apartments from page"""
        apartments = []
        
        # Try multiple possible selectors for listing items
        selectors = [
            'div[data-test="item"]',  # Modern krisha.kz
            'div.a-search-item',      # Alternative selector
            'div[class*="item"]',     # Generic item class
            'a[href*="/show/"]',      # Links to individual listings
        ]
        
        items = None
        for selector in selectors:
            items = self.soup.select(selector)
            if items:
                logger.info(f"Found {len(items)} items using selector: {selector}")
                break
        
        if not items:
            logger.warning("No listing items found on page")
            return apartments
        
        for item in items:
            try:
                apartment = self._parse_item(item)
                if apartment:
                    apartments.append(apartment)
            except Exception as e:
                logger.error(f"Error parsing item: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(apartments)} apartments from page")
        return apartments
    
    def _parse_item(self, item) -> Optional[Apartment]:
        """Parse single listing item"""
        
        # Extract link and ID
        link = self._extract_link(item)
        if not link:
            return None
        
        krisha_id = self._extract_id_from_link(link)
        if not krisha_id:
            return None
        
        # Extract basic information
        title = self._extract_text(item, ['h2', 'h3', '[class*="title"]', '[class*="heading"]'])
        address = self._extract_address(item, title)
        price = self._extract_price(item)
        
        if not price or not address:
            logger.debug(f"Skipping item {krisha_id}: missing price or address")
            return None
        
        # Extract apartment details
        rooms = self._extract_rooms(title, address)
        area = self._extract_area(title, address)
        jk_name = self._extract_jk_name(item, address)
        
        # Calculate price per sqm
        price_per_sqm = self._calculate_price_per_sqm(price, area) if area else 0
        
        # Extract additional info
        description = self._extract_description(item)
        photos_count = self._extract_photos_count(item)
        seller_type = self._extract_seller_type(item)
        phone = self._extract_phone(item)
        
        # Get district from config
        district = self.config.search_params.city_name
        
        apartment = Apartment(
            krisha_id=krisha_id,
            jk_name=jk_name,
            district=district,
            address=address,
            price=price,
            area=area,
            rooms=rooms,
            price_per_sqm=price_per_sqm,
            description=description,
            photos_count=photos_count,
            phone=phone,
            seller_type=seller_type,
            url=link,
            parsed_at=datetime.now(),
        )
        
        logger.debug(f"Parsed apartment: {krisha_id} - {address} - {price}₸")
        return apartment
    
    def _extract_link(self, item) -> Optional[str]:
        """Extract listing link"""
        # Try multiple link selectors
        link_selectors = [
            'a[href*="/show/"]',
            'a[href*="/kvartiry/"]',
            'a[data-test="listing-link"]',
            'a.a-search-item__link',
        ]
        
        for selector in link_selectors:
            link_elem = item.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                if href.startswith('/'):
                    return urljoin(self.BASE_URL, href)
                return href
        
        return None
    
    def _extract_id_from_link(self, link: str) -> Optional[str]:
        """Extract krisha.kz ID from link"""
        # Pattern: /show/123456789/
        match = re.search(r'/show/(\d+)', link)
        if match:
            return match.group(1)
        return None
    
    def _extract_text(self, item, selectors: list) -> str:
        """Extract text from element using multiple selectors"""
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text:
                    return text
        return ""
    
    def _extract_rooms(self, title: str, address: str) -> int:
        """Extract number of rooms from title or address"""
        text = f"{title} {address}".lower()
        
        # Patterns: "1-комнатная", "2-комнатная", etc.
        match = re.search(r'(\d+)[^\d]*комнат', text)
        if match:
            return int(match.group(1))
        
        # Alternative: "1 room", etc
        match = re.search(r'(\d)\s*к\.?\s*кв', text)
        if match:
            return int(match.group(1))
        
        # Studio/студия = 0 rooms (or 1)
        if 'студ' in text:
            return 0
        
        return 1  # Default to 1 room
    
    def _extract_area(self, title: str, address: str) -> Optional[float]:
        """Extract area in square meters"""
        text = f"{title} {address}"
        
        # Pattern: "68 м²" or "68 м2" or "68 кв.м"
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*м[²2]', text)
        if match:
            area_str = match.group(1).replace(',', '.')
            return float(area_str)
        
        return None
    
    def _extract_price(self, item) -> Optional[int]:
        """Extract price in tengo"""
        price_selectors = [
            '[class*="price"]',
            '[data-test="price"]',
            'span[class*="amount"]',
        ]
        
        for selector in price_selectors:
            price_elem = item.select_one(selector)
            if price_elem:
                text = price_elem.get_text(strip=True)
                # Remove spaces and non-digit characters except numbers
                price_str = re.sub(r'[^\d]', '', text)
                if price_str:
                    return int(price_str)
        
        return None
    
    def _extract_address(self, item, title: str) -> Optional[str]:
        """Extract address"""
        address_selectors = [
            '[class*="address"]',
            '[class*="location"]',
            'p[class*="address"]',
            'span[class*="address"]',
        ]
        
        for selector in address_selectors:
            addr_elem = item.select_one(selector)
            if addr_elem:
                text = addr_elem.get_text(strip=True)
                if text and len(text) > 3:
                    return text
        
        # Try to extract from title if not found
        # Usually format: "2-комнатная квартира · 68 м² · 6/12 этаж"
        # Address part comes after
        if title:
            parts = title.split('·')
            if len(parts) > 1:
                return parts[-1].strip()
        
        return None
    
    def _extract_jk_name(self, item, address: str) -> Optional[str]:
        """Extract residential complex (ЖК) name"""
        jk_selectors = [
            '[class*="complex"]',
            '[class*="building"]',
            'span[class*="jk"]',
        ]
        
        for selector in jk_selectors:
            jk_elem = item.select_one(selector)
            if jk_elem:
                text = jk_elem.get_text(strip=True)
                if text and len(text) > 2:
                    return text
        
        # Try to extract from address (usually first part before comma)
        if address:
            parts = address.split(',')
            if len(parts) > 0:
                potential_jk = parts[0].strip()
                # ЖК names usually don't contain numbers only
                if potential_jk and not potential_jk.replace('-', '').isdigit():
                    return potential_jk
        
        return None
    
    def _extract_description(self, item) -> Optional[str]:
        """Extract listing description"""
        desc_selectors = [
            '[class*="description"]',
            '[class*="details"]',
            'p[class*="desc"]',
        ]
        
        for selector in desc_selectors:
            desc_elem = item.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                if text:
                    return text[:500]  # Limit to 500 chars
        
        return None
    
    def _extract_photos_count(self, item) -> int:
        """Extract number of photos"""
        # Look for photo count indicator
        photo_selectors = [
            '[class*="photo-count"]',
            'span[class*="count"]',
        ]
        
        for selector in photo_selectors:
            photo_elem = item.select_one(selector)
            if photo_elem:
                text = photo_elem.get_text(strip=True)
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
        
        # Default to 1 if has image
        if item.select_one('img'):
            return 1
        
        return 0
    
    def _extract_seller_type(self, item) -> str:
        """Extract seller type (owner/agency/realtor)"""
        text = item.get_text().lower()
        
        if 'агент' in text or 'agency' in text:
            return 'agency'
        elif 'риэлтор' in text or 'realtor' in text:
            return 'realtor'
        elif 'владелец' in text or 'owner' in text:
            return 'owner'
        
        return 'unknown'
    
    def _extract_phone(self, item) -> Optional[str]:
        """Extract phone number"""
        text = item.get_text()
        
        # Kazakhstan phone patterns
        patterns = [
            r'\+7\d{10}',
            r'7\d{10}',
            r'\(\d{3}\)\s*\d{3}[- ]?\d{2}[- ]?\d{2}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    @staticmethod
    def _calculate_price_per_sqm(price: int, area: Optional[float]) -> float:
        """Calculate price per square meter"""
        if not area or area == 0:
            return 0
        return round(price / area, 2)
