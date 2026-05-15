from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY", "03US815ciVS9pnXYWG4XUd9oAvRiMAUV")

@app.route('/')
def home():
    return jsonify({"message": "Ticket Bot API is running!", "status": "active"})

@app.route('/seatmap/<event_id>')
def seatmap_page(event_id):
    """Serve the interactive seat map page"""
    return render_template('index.html', event_id=event_id)

@app.route('/api/search')
def search_events():
    """Search for events using Ticketmaster API"""
    keyword = request.args.get('q', '')
    
    if not keyword:
        return jsonify({'events': []})
    
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': TICKETMASTER_API_KEY,
        'keyword': keyword,
        'size': 20,
        'sort': 'date,asc',
        'countryCode': 'US'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        events = []
        if '_embedded' in data and 'events' in data['_embedded']:
            for event in data['_embedded']['events']:
                venue = event.get('_embedded', {}).get('venues', [{}])[0]
                
                # Get price range
                price_ranges = event.get('priceRanges', [])
                price_range = f"${price_ranges[0]['min']} - ${price_ranges[0]['max']}" if price_ranges else "Check website"
                
                events.append({
                    'id': event['id'],
                    'name': event['name'],
                    'date': event.get('dates', {}).get('start', {}).get('localDate', 'TBA'),
                    'time': event.get('dates', {}).get('start', {}).get('localTime', 'TBA'),
                    'venue': venue.get('name', 'TBA'),
                    'venue_id': venue.get('id', ''),
                    'city': venue.get('city', {}).get('name', ''),
                    'price_range': price_range,
                    'image': event.get('images', [{}])[0].get('url', ''),
                    'status': event.get('dates', {}).get('status', {}).get('code', 'onsale')
                })
        
        return jsonify({'events': events})
        
    except requests.exceptions.RequestException as e:
        return jsonify({'events': [], 'error': str(e)}), 500

@app.route('/api/event/<event_id>')
def get_event_details(event_id):
    """Get detailed event information"""
    url = f"https://app.ticketmaster.com/discovery/v2/events/{event_id}.json"
    params = {'apikey': TICKETMASTER_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        venue = data.get('_embedded', {}).get('venues', [{}])[0]
        
        event_details = {
            'id': data['id'],
            'name': data['name'],
            'date': data.get('dates', {}).get('start', {}).get('localDate', 'TBA'),
            'venue': venue.get('name', 'TBA'),
            'address': venue.get('address', {}).get('line1', ''),
            'city': venue.get('city', {}).get('name', ''),
            'seatmap': data.get('seatmap', {}).get('staticUrl', ''),
        }
        
        return jsonify(event_details)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/seatmap/<event_id>')
def get_seatmap_data(event_id):
    """Return venue and seat data for interactive seat map"""
    
    try:
        # Get event details
        event_url = f"https://app.ticketmaster.com/discovery/v2/events/{event_id}.json"
        event_response = requests.get(event_url, params={'apikey': TICKETMASTER_API_KEY}, timeout=10)
        event_data = event_response.json()
        
        venue = event_data.get('_embedded', {}).get('venues', [{}])[0]
        venue_name = venue.get('name', 'Venue')
        event_name = event_data.get('name', 'Event')
        
        # Get venue layout if available
        venue_id = venue.get('id')
        seatmap_image = event_data.get('seatmap', {}).get('staticUrl', '')
        
        # Create simulated sections (since Ticketmaster API doesn't provide seat-level data)
        # In a real implementation, you'd fetch this from a database or another source
        sections = [
            {'id': '101', 'name': '101', 'rows': 8, 'seats_per_row': 8, 'price': 89},
            {'id': '102', 'name': '102', 'rows': 8, 'seats_per_row': 8, 'price': 89},
            {'id': '103', 'name': '103', 'rows': 8, 'seats_per_row': 8, 'price': 129},
            {'id': '104', 'name': '104', 'rows': 8, 'seats_per_row': 8, 'price': 129},
            {'id': '105', 'name': '105', 'rows': 8, 'seats_per_row': 8, 'price': 159},
            {'id': '106', 'name': '106', 'rows': 8, 'seats_per_row': 8, 'price': 159},
            {'id': '107', 'name': '107', 'rows': 8, 'seats_per_row': 8, 'price': 199},
            {'id': '108', 'name': '108', 'rows': 8, 'seats_per_row': 8, 'price': 199},
        ]
        
        # Simulate some taken seats randomly (for demo)
        import random
        for section in sections:
            taken = []
            # 20-40% of seats are taken
            total_seats = section['rows'] * section['seats_per_row']
            num_taken = int(total_seats * random.uniform(0.2, 0.4))
            
            rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            for _ in range(num_taken):
                row = random.choice(rows)
                seat = random.randint(1, section['seats_per_row'])
                taken.append(f"{section['name']}-{row}{seat}")
            
            section['taken_seats'] = list(set(taken))  # Remove duplicates
        
        seatmap_data = {
            'event_id': event_id,
            'event_name': event_name,
            'venue': venue_name,
            'seatmap_image': seatmap_image,
            'sections': sections,
            'max_seats': 4
        }
        
        return jsonify(seatmap_data)
        
    except Exception as e:
        return jsonify({'error': str(e), 'sections': []}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)