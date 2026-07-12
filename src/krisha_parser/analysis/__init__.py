"""Data analysis and metrics calculation"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import sqlite3
import pandas as pd
from statistics import median

from krisha_parser.db.models import Apartment, JKMetrics
from krisha_parser.db.service import get_connection

logger = logging.getLogger()


class DataAnalyzer:
    """Analyze real estate market data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = get_connection(db_path)
    
    def calculate_jk_metrics(self, district: Optional[str] = None) -> List[JKMetrics]:
        """
        Calculate aggregated metrics for residential complexes (ЖК)
        
        Args:
            district: Filter by district (optional)
        
        Returns:
            List of JKMetrics objects
        """
        query = "SELECT * FROM apartments WHERE 1=1"
        params = []
        
        if district:
            query += " AND district = ?"
            params.append(district)
        
        query += " AND jk_name IS NOT NULL"
        
        df = pd.read_sql_query(query, self.conn, params=params)
        
        if df.empty:
            logger.warning("No apartments with JK names found")
            return []
        
        metrics_list = []
        
        # Group by JK name and district
        for (jk_name, dist), group in df.groupby(['jk_name', 'district']):
            metric = self._calculate_single_jk_metric(jk_name, dist, group)
            if metric:
                metrics_list.append(metric)
        
        logger.info(f"Calculated metrics for {len(metrics_list)} JK complexes")
        return metrics_list
    
    def _calculate_single_jk_metric(
        self, 
        jk_name: str, 
        district: str, 
        group: pd.DataFrame
    ) -> Optional[JKMetrics]:
        """Calculate metrics for a single JK"""
        
        try:
            prices = group['price'].dropna()
            areas = group['area'].dropna()
            rooms = group['rooms'].dropna()
            
            if len(prices) == 0:
                return None
            
            metric = JKMetrics(
                jk_name=jk_name,
                district=district,
                avg_price=float(prices.mean()),
                avg_price_per_sqm=float(group['price_per_sqm'].mean()),
                avg_area=float(areas.mean()) if len(areas) > 0 else 0,
                median_price=float(median(prices)),
                count_total=int(len(group)),
                count_1room=int(len(group[group['rooms'] == 1])),
                count_2room=int(len(group[group['rooms'] == 2])),
                count_3plus_room=int(len(group[group['rooms'] >= 3])),
                min_price=int(prices.min()),
                max_price=int(prices.max()),
                snapshot_date=datetime.now().strftime('%Y-%m-%d'),
            )
            
            return metric
        except Exception as e:
            logger.error(f"Error calculating metrics for {jk_name}: {e}")
            return None
    
    def save_jk_metrics(self, metrics: List[JKMetrics]) -> int:
        """Save JK metrics to database"""
        cursor = self.conn.cursor()
        saved_count = 0
        
        for metric in metrics:
            try:
                cursor.execute("""
                    INSERT INTO jk_metrics 
                    (jk_name, district, avg_price, avg_price_per_sqm, avg_area, 
                     median_price, count_total, count_1room, count_2room, count_3plus_room,
                     min_price, max_price, snapshot_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.jk_name,
                    metric.district,
                    metric.avg_price,
                    metric.avg_price_per_sqm,
                    metric.avg_area,
                    metric.median_price,
                    metric.count_total,
                    metric.count_1room,
                    metric.count_2room,
                    metric.count_3plus_room,
                    metric.min_price,
                    metric.max_price,
                    metric.snapshot_date,
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving metrics for {metric.jk_name}: {e}")
        
        self.conn.commit()
        logger.info(f"Saved {saved_count} JK metrics to database")
        return saved_count
    
    def get_district_summary(self, district: str) -> Dict:
        """Get summary statistics for a district"""
        query = """
            SELECT 
                COUNT(*) as total_apartments,
                AVG(price) as avg_price,
                MEDIAN(price) as median_price,
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(area) as avg_area,
                AVG(price_per_sqm) as avg_price_per_sqm,
                COUNT(DISTINCT jk_name) as jk_count
            FROM apartments
            WHERE district = ?
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (district,))
        result = cursor.fetchone()
        
        if not result:
            return {}
        
        return {
            'total_apartments': result[0],
            'avg_price': result[1],
            'median_price': result[2],
            'min_price': result[3],
            'max_price': result[4],
            'avg_area': result[5],
            'avg_price_per_sqm': result[6],
            'jk_count': result[7],
        }
    
    def get_top_jk_by_price(
        self, 
        district: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get top JK by average price"""
        query = """
            SELECT 
                jk_name,
                district,
                COUNT(*) as count,
                AVG(price) as avg_price,
                AVG(price_per_sqm) as avg_price_per_sqm,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM apartments
            WHERE jk_name IS NOT NULL
        """
        params = []
        
        if district:
            query += " AND district = ?"
            params.append(district)
        
        query += " GROUP BY jk_name, district ORDER BY avg_price DESC LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql_query(query, self.conn, params=params)
        
        return df.to_dict('records') if not df.empty else []
    
    def get_price_dynamics(
        self,
        jk_name: str,
        days: int = 30
    ) -> List[Dict]:
        """Get price dynamics for a JK over time"""
        query = """
            SELECT 
                DATE(parsed_at) as date,
                AVG(price) as avg_price,
                AVG(price_per_sqm) as avg_price_per_sqm,
                COUNT(*) as count
            FROM apartments
            WHERE jk_name = ?
            AND parsed_at > datetime('now', '-' || ? || ' days')
            GROUP BY DATE(parsed_at)
            ORDER BY date ASC
        """
        
        df = pd.read_sql_query(query, self.conn, params=[jk_name, days])
        
        return df.to_dict('records') if not df.empty else []
    
    def get_investment_score(
        self,
        jk_name: str,
        district: str
    ) -> Dict:
        """
        Calculate investment attractiveness score for a JK
        
        Factors:
        - Price per sqm compared to district average
        - Supply (number of listings)
        - Price dynamics (trend)
        
        Returns score 0-100
        """
        
        # Get JK metrics
        query = """
            SELECT 
                COUNT(*) as count,
                AVG(price_per_sqm) as jk_avg_price_sqm,
                AVG(price) as jk_avg_price
            FROM apartments
            WHERE jk_name = ? AND district = ?
        """
        
        df = pd.read_sql_query(query, self.conn, params=[jk_name, district])
        
        if df.empty or df.iloc[0]['count'] < 3:
            return {'score': 0, 'reason': 'Insufficient data'}
        
        jk_data = df.iloc[0]
        
        # Get district average
        district_query = """
            SELECT AVG(price_per_sqm) as avg_price_sqm
            FROM apartments
            WHERE district = ?
        """
        
        district_df = pd.read_sql_query(district_query, self.conn, params=[district])
        district_avg = district_df.iloc[0]['avg_price_sqm'] if not district_df.empty else 0
        
        score = 0
        factors = {}
        
        # Factor 1: Price comparison (0-40 points)
        # Lower price per sqm = higher score
        if district_avg > 0:
            price_ratio = jk_data['jk_avg_price_sqm'] / district_avg
            if price_ratio < 0.9:
                factors['price_advantage'] = 40
                score += 40
            elif price_ratio < 1.0:
                factors['price_advantage'] = 25
                score += 25
            else:
                factors['price_advantage'] = 10
                score += 10
        
        # Factor 2: Supply level (0-30 points)
        # More listings = more liquid market
        if jk_data['count'] >= 20:
            factors['supply'] = 30
            score += 30
        elif jk_data['count'] >= 10:
            factors['supply'] = 20
            score += 20
        else:
            factors['supply'] = 10
            score += 10
        
        # Factor 3: Price trend (0-30 points)
        dynamics = self.get_price_dynamics(jk_name, days=30)
        if len(dynamics) >= 2:
            recent_price = dynamics[-1]['avg_price_per_sqm']
            old_price = dynamics[0]['avg_price_per_sqm']
            
            price_change = ((recent_price - old_price) / old_price) * 100 if old_price > 0 else 0
            
            if price_change < -5:  # Price decreased
                factors['trend'] = 30
                score += 30
            elif price_change < 0:  # Slight decrease
                factors['trend'] = 20
                score += 20
            elif price_change < 5:  # Stable
                factors['trend'] = 15
                score += 15
            else:
                factors['trend'] = 5  # Price increased
                score += 5
        
        return {
            'jk_name': jk_name,
            'district': district,
            'score': min(score, 100),
            'factors': factors,
            'avg_price_per_sqm': round(jk_data['jk_avg_price_sqm'], 2),
            'district_avg_price_per_sqm': round(district_avg, 2),
            'listings_count': jk_data['count'],
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()
