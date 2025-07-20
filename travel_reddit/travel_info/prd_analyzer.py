"""
PRD Analysis Tool for r/koreatravel Data
Implements the Product Requirements Document for analyzing scraped Reddit data
"""

import pandas as pd
import os
import re
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger_eng')

class PRDAnalyzer:
    """Analyzes r/koreatravel data according to PRD specifications"""
    
    def __init__(self, data_dir: str = "prd_data"):
        """Initialize the analyzer with data directory"""
        self.data_dir = data_dir
        self.flair_data = {}
        self.analysis_results = {}
        self.stop_words = set(stopwords.words('english'))
        
        # Flair mappings (from filename to display name)
        self.flair_mapping = {
            'places_to_visit': 'Places to Visit',
            'itinerary': 'Itinerary', 
            'trip_report': 'Trip Report',
            'activities_and_events': 'Activities & Events',
            'k-beauty': 'K-Beauty',
            'emergency': 'Emergency',
            'money_and_budget': 'Money & Budget',
            'transit_and_flight': 'Transit & Flight',
            'shopping_and_services': 'Shopping & Services'
        }
    
    def load_data(self):
        """Load all CSV files from the data directory"""
        print("📂 Loading CSV files from prd_data directory...")
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(self.data_dir, filename)
                
                # Extract flair from filename
                parts = filename.replace('prd_', '').replace('.csv', '').split('_')
                
                # Handle multi-word flairs
                if 'posts' in parts:
                    posts_index = parts.index('posts')
                    flair_parts = parts[:posts_index]  # Everything before 'posts'
                    data_type = 'posts'
                elif 'comments' in parts:
                    comments_index = parts.index('comments')
                    flair_parts = parts[:comments_index]  # Everything before 'comments'
                    data_type = 'comments'
                else:
                    continue
                
                flair_key = '_'.join(flair_parts)
                
                if flair_key not in self.flair_data:
                    self.flair_data[flair_key] = {}
                
                # Load the data
                try:
                    df = pd.read_csv(filepath)
                    self.flair_data[flair_key][data_type] = df
                    print(f"✅ Loaded {len(df)} rows from {filename}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")
        
        print(f"📊 Loaded data for {len(self.flair_data)} flair categories")
    
    def extract_keywords(self, text_list: List[str], min_frequency: int = 30) -> List[Tuple[str, int]]:
        """
        Extract keywords (nouns and noun phrases) from text
        Returns list of (keyword, frequency) tuples
        """
        # Combine all text
        combined_text = ' '.join(str(text) for text in text_list if pd.notna(text))
        
        # Tokenize and get POS tags
        tokens = word_tokenize(combined_text.lower())
        pos_tags = pos_tag(tokens)
        
        # Extract nouns and noun phrases
        keywords = []
        current_phrase = []
        
        for word, tag in pos_tags:
            # Clean word
            word = re.sub(r'[^a-zA-Z0-9\s]', '', word)
            if len(word) < 2 or word in self.stop_words:
                if current_phrase:
                    phrase = ' '.join(current_phrase)
                    if len(phrase) > 2:
                        keywords.append(phrase)
                    current_phrase = []
                continue
            
            # Check if it's a noun
            if tag.startswith('NN'):
                current_phrase.append(word)
            else:
                if current_phrase:
                    phrase = ' '.join(current_phrase)
                    if len(phrase) > 2:
                        keywords.append(phrase)
                    current_phrase = []
        
        # Add final phrase
        if current_phrase:
            phrase = ' '.join(current_phrase)
            if len(phrase) > 2:
                keywords.append(phrase)
        
        # Count frequencies
        keyword_counts = Counter(keywords)
        
        # Filter by minimum frequency
        filtered_keywords = [(kw, count) for kw, count in keyword_counts.items() 
                           if count >= min_frequency]
        
        return sorted(filtered_keywords, key=lambda x: x[1], reverse=True)
    
    def get_popular_posts(self, posts_df: pd.DataFrame, percentile: float = 85.0) -> pd.DataFrame:
        """Get posts in the top 15% by score"""
        if posts_df.empty:
            return posts_df
        
        threshold = np.percentile(posts_df['score'], percentile)
        return posts_df[posts_df['score'] >= threshold]
    
    def find_evidence_quotes(self, text_list: List[str], urls_list: List[str], 
                           keyword: str, max_quotes: int = 3) -> List[Dict[str, str]]:
        """Find evidence quotes containing the keyword"""
        quotes = []
        
        for text, url in zip(text_list, urls_list):
            if pd.isna(text) or pd.isna(url):
                continue
                
            text = str(text)
            sentences = sent_tokenize(text)
            
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    # Clean and truncate sentence
                    clean_sentence = re.sub(r'\s+', ' ', sentence.strip())
                    if len(clean_sentence) > 200:
                        clean_sentence = clean_sentence[:200] + "..."
                    
                    quotes.append({
                        'quote': clean_sentence,
                        'url': str(url)
                    })
                    
                    if len(quotes) >= max_quotes:
                        return quotes
        
        return quotes
    
    def analyze_places_to_visit(self):
        """Analyze Places to Visit according to PRD requirements"""
        print("\n🏛️ Analyzing Places to Visit...")
        
        flair_key = 'places_to_visit'
        if flair_key not in self.flair_data:
            return
        
        posts_df = self.flair_data[flair_key].get('posts', pd.DataFrame())
        comments_df = self.flair_data[flair_key].get('comments', pd.DataFrame())
        
        # Combine text for keyword analysis
        all_text = []
        all_urls = []
        
        for _, row in posts_df.iterrows():
            if pd.notna(row.get('title')):
                all_text.append(str(row['title']))
                all_urls.append(str(row.get('full_reddit_url', '')))
            if pd.notna(row.get('selftext')):
                all_text.append(str(row['selftext']))
                all_urls.append(str(row.get('full_reddit_url', '')))
        
        for _, row in comments_df.iterrows():
            if pd.notna(row.get('body')):
                all_text.append(str(row['body']))
                all_urls.append(str(row.get('full_reddit_url', '')))
        
        # Extract high-level locations (cities/provinces)
        keywords = self.extract_keywords(all_text, min_frequency=30)
        
        # Filter for likely locations (heuristic approach)
        location_keywords = []
        for keyword, freq in keywords[:20]:  # Check top 20 keywords
            # Simple heuristic: locations are often capitalized in original text
            if any(word[0].isupper() for word in keyword.split() if len(word) > 2):
                location_keywords.append((keyword, freq))
        
        top_locations = location_keywords[:5]
        
        result = {
            'type': 'nested_locations',
            'data': {}
        }
        
        # For each top location, find mid-level locations
        for location, freq in top_locations:
            print(f"  📍 Analyzing {location} (mentioned {freq} times)")
            
            # Find text mentioning this location
            location_texts = []
            location_urls = []
            
            for text, url in zip(all_text, all_urls):
                if location.lower() in text.lower():
                    location_texts.append(text)
                    location_urls.append(url)
            
            # Extract sub-locations from texts mentioning this location
            sub_keywords = self.extract_keywords(location_texts, min_frequency=5)
            sub_locations = [kw for kw, freq in sub_keywords[:5] if kw.lower() != location.lower()]
            
            # Get evidence for this location
            evidence = self.find_evidence_quotes(all_text, all_urls, location)
            
            result['data'][location] = {
                'frequency': freq,
                'sub_locations': sub_locations,
                'evidence': evidence
            }
        
        self.analysis_results['Places to Visit'] = result
    
    def analyze_itinerary_trip_report(self):
        """Analyze Itinerary and Trip Report for abstract themes"""
        print("\n📋 Analyzing Itinerary and Trip Report...")
        
        combined_data = {'posts': [], 'comments': []}
        
        # Combine data from both categories
        for flair_key in ['itinerary', 'trip_report']:
            if flair_key in self.flair_data:
                posts_df = self.flair_data[flair_key].get('posts', pd.DataFrame())
                comments_df = self.flair_data[flair_key].get('comments', pd.DataFrame())
                
                if not posts_df.empty:
                    combined_data['posts'].append(posts_df)
                if not comments_df.empty:
                    combined_data['comments'].append(comments_df)
        
        # Concatenate dataframes only if we have data
        all_posts = pd.concat(combined_data['posts'], ignore_index=True) if combined_data['posts'] else pd.DataFrame()
        all_comments = pd.concat(combined_data['comments'], ignore_index=True) if combined_data['comments'] else pd.DataFrame()
        
        # Check if we have any posts data
        if all_posts.empty:
            print("  ⚠️ No posts data found for Itinerary & Trip Report analysis")
            self.analysis_results['Itinerary & Trip Report'] = {
                'type': 'themes',
                'data': []
            }
            return
        
        # Get popular posts only
        popular_posts = self.get_popular_posts(all_posts)
        
        # Combine text from popular posts and their comments
        popular_text = []
        popular_urls = []
        
        for _, row in popular_posts.iterrows():
            if pd.notna(row.get('title')):
                popular_text.append(str(row['title']))
                popular_urls.append(str(row.get('full_reddit_url', '')))
            if pd.notna(row.get('selftext')):
                popular_text.append(str(row['selftext']))
                popular_urls.append(str(row.get('full_reddit_url', '')))
        
        # Add comments from popular posts if we have posts and comments data
        if not popular_posts.empty and not all_comments.empty and 'post_id' in popular_posts.columns:
            popular_post_ids = set(popular_posts['post_id'].astype(str))
            for _, row in all_comments.iterrows():
                if str(row.get('post_id', '')) in popular_post_ids and pd.notna(row.get('body')):
                    popular_text.append(str(row['body']))
                    popular_urls.append(str(row.get('full_reddit_url', '')))
        
        # Extract themes (use longer phrases as themes)
        keywords = self.extract_keywords(popular_text, min_frequency=10)
        
        # Filter for theme-like keywords (longer phrases, advice-related)
        themes = []
        for keyword, freq in keywords:
            if len(keyword.split()) >= 2:  # Multi-word phrases are more likely to be themes
                evidence = self.find_evidence_quotes(popular_text, popular_urls, keyword)
                if evidence:  # Only include if we have evidence
                    themes.append({
                        'theme': keyword,
                        'frequency': freq,
                        'evidence': evidence
                    })
        
        self.analysis_results['Itinerary & Trip Report'] = {
            'type': 'themes',
            'data': themes[:5]  # Top 5 themes
        }
    
    def analyze_activities_events(self):
        """Analyze Activities & Events for specific activities"""
        print("\n🎯 Analyzing Activities & Events...")
        
        flair_key = 'activities_and_events'
        if flair_key not in self.flair_data:
            return
        
        posts_df = self.flair_data[flair_key].get('posts', pd.DataFrame())
        comments_df = self.flair_data[flair_key].get('comments', pd.DataFrame())
        
        # Combine all text
        all_text = []
        all_urls = []
        
        for _, row in posts_df.iterrows():
            if pd.notna(row.get('title')):
                all_text.append(str(row['title']))
                all_urls.append(str(row.get('full_reddit_url', '')))
            if pd.notna(row.get('selftext')):
                all_text.append(str(row['selftext']))
                all_urls.append(str(row.get('full_reddit_url', '')))
        
        for _, row in comments_df.iterrows():
            if pd.notna(row.get('body')):
                all_text.append(str(row['body']))
                all_urls.append(str(row.get('full_reddit_url', '')))
        
        # Extract activity keywords
        keywords = self.extract_keywords(all_text, min_frequency=15)
        
        activities = []
        for keyword, freq in keywords[:10]:  # Check top 10
            # Get evidence
            evidence = self.find_evidence_quotes(all_text, all_urls, keyword)
            if evidence:
                activities.append({
                    'activity': keyword,
                    'frequency': freq,
                    'evidence': evidence
                })
        
        self.analysis_results['Activities & Events'] = {
            'type': 'activities',
            'data': activities[:5]  # Top 5 activities
        }
    
    def analyze_other_categories(self):
        """Analyze other categories for common questions/themes"""
        print("\n🔍 Analyzing other categories...")
        
        other_categories = ['k-beauty', 'emergency', 'money_and_budget', 'transit_and_flight']
        
        for flair_key in other_categories:
            if flair_key not in self.flair_data:
                continue
                
            display_name = self.flair_mapping.get(flair_key, flair_key.replace('_', ' ').title())
            print(f"  📊 Analyzing {display_name}")
            
            posts_df = self.flair_data[flair_key].get('posts', pd.DataFrame())
            comments_df = self.flair_data[flair_key].get('comments', pd.DataFrame())
            
            # Focus on post titles for questions/themes
            titles = [str(row['title']) for _, row in posts_df.iterrows() if pd.notna(row.get('title'))]
            title_urls = [str(row.get('full_reddit_url', '')) for _, row in posts_df.iterrows()]
            
            # Also include comment text
            comment_text = [str(row['body']) for _, row in comments_df.iterrows() if pd.notna(row.get('body'))]
            comment_urls = [str(row.get('full_reddit_url', '')) for _, row in comments_df.iterrows()]
            
            all_text = titles + comment_text
            all_urls = title_urls + comment_urls
            
            # Extract themes/questions
            keywords = self.extract_keywords(all_text, min_frequency=5)
            
            themes = []
            for keyword, freq in keywords[:8]:  # Check top 8
                evidence = self.find_evidence_quotes(all_text, all_urls, keyword)
                if evidence:
                    themes.append({
                        'theme': keyword,
                        'frequency': freq,
                        'evidence': evidence
                    })
            
            self.analysis_results[display_name] = {
                'type': 'themes',
                'data': themes[:5]  # Top 5 themes
            }
    
    def generate_report(self, output_file: str = "prd_intelligence_report.md"):
        """Generate the final intelligence report in Markdown format"""
        print(f"\n📝 Generating intelligence report: {output_file}")
        
        report_lines = []
        
        # Header
        report_lines.extend([
            "# r/koreatravel Intelligence Report",
            "",
            f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "**Data Source:** r/koreatravel subreddit (PRD analysis)",
            "",
            "---",
            ""
        ])
        
        # Executive Summary
        report_lines.extend([
            "## Executive Summary",
            "",
            "This report analyzes scraped data from r/koreatravel to identify key travel trends, popular destinations, and common traveler concerns. Key findings include:",
            ""
        ])
        
        # Add high-level findings
        if 'Places to Visit' in self.analysis_results:
            places_data = self.analysis_results['Places to Visit']['data']
            top_place = list(places_data.keys())[0] if places_data else "N/A"
            report_lines.append(f"- **Most Discussed Destination:** {top_place}")
        
        if 'Activities & Events' in self.analysis_results:
            activities = self.analysis_results['Activities & Events']['data']
            top_activity = activities[0]['activity'] if activities else "N/A"
            report_lines.append(f"- **Most Popular Activity:** {top_activity}")
        
        report_lines.extend(["", "---", ""])
        
        # Detailed Analysis by Category
        report_lines.extend([
            "## Detailed Analysis by Category",
            ""
        ])
        
        for category, data in self.analysis_results.items():
            report_lines.extend([
                f"### {category}",
                ""
            ])
            
            if data['type'] == 'nested_locations':
                report_lines.append("**Top Destinations and Attractions:**")
                report_lines.append("")
                
                for location, location_data in data['data'].items():
                    report_lines.append(f"#### {location} ({location_data['frequency']} mentions)")
                    report_lines.append("")
                    
                    if location_data['sub_locations']:
                        report_lines.append("**Popular attractions/areas:**")
                        for sub_loc in location_data['sub_locations']:
                            report_lines.append(f"- {sub_loc}")
                        report_lines.append("")
                    
                    report_lines.append("**Evidence:**")
                    for evidence in location_data['evidence']:
                        report_lines.append(f'- "{evidence["quote"]}" - [{evidence["url"]}]({evidence["url"]})')
                    report_lines.append("")
            
            elif data['type'] == 'activities':
                report_lines.append("**Most Discussed Activities:**")
                report_lines.append("")
                
                for i, activity_data in enumerate(data['data'], 1):
                    report_lines.append(f"{i}. **{activity_data['activity']}** ({activity_data['frequency']} mentions)")
                    report_lines.append("")
                    report_lines.append("   **Evidence:**")
                    for evidence in activity_data['evidence']:
                        report_lines.append(f'   - "{evidence["quote"]}" - [{evidence["url"]}]({evidence["url"]})')
                    report_lines.append("")
            
            elif data['type'] == 'themes':
                if category == 'Itinerary & Trip Report':
                    report_lines.append("**Key Travel Themes from Popular Posts:**")
                else:
                    report_lines.append("**Common Questions and Topics:**")
                report_lines.append("")
                
                for theme_data in data['data']:
                    report_lines.append(f"- **{theme_data['theme']}** ({theme_data['frequency']} mentions)")
                    report_lines.append("")
                    report_lines.append("  **Evidence:**")
                    for evidence in theme_data['evidence']:
                        report_lines.append(f'  - "{evidence["quote"]}" - [{evidence["url"]}]({evidence["url"]})')
                    report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        # Conclusion
        report_lines.extend([
            "## Conclusion",
            "",
            "This analysis reveals the primary interests and concerns of travelers to Korea as discussed on Reddit. The data shows clear patterns in:",
            "",
            "- **Popular destinations** and specific attractions within them",
            "- **Common activities** that travelers engage in or ask about", 
            "- **Recurring themes** in trip planning and experiences",
            "- **Frequent questions** across different travel categories",
            "",
            "All findings are supported by direct quotes and verifiable Reddit URLs as evidence.",
            "",
            "---",
            "",
            "*Report generated by PRD Analyzer*"
        ])
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✅ Report saved to {output_file}")
    
    def run_full_analysis(self):
        """Run the complete PRD analysis workflow"""
        print("🚀 Starting PRD Analysis Workflow")
        print("=" * 50)
        
        # Step 1: Load data
        self.load_data()
        
        if not self.flair_data:
            print("❌ No data found. Please ensure CSV files are in the prd_data directory.")
            return
        
        # Step 2: Perform thematic analysis by category
        print("\n📊 Step 2: Performing Thematic Analysis by Category")
        
        self.analyze_places_to_visit()
        self.analyze_itinerary_trip_report()
        self.analyze_activities_events()
        self.analyze_other_categories()
        
        # Step 3: Generate final report
        print("\n📋 Step 3: Consolidating into Final Report")
        self.generate_report()
        
        print("\n✅ PRD Analysis Complete!")
        print("📂 Check 'prd_intelligence_report.md' for the final report")


def main():
    """Main execution function"""
    analyzer = PRDAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()