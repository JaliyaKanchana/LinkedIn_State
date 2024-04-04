from flask import Flask, jsonify, request
from functions import scrape_linkedin  

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def api_scrape():
    content = request.json
    profile_url = content.get('profile_url')
    
    if not profile_url:
        return jsonify({'error': 'Profile URL is required.'}), 400

    try:
        data = scrape_linkedin(profile_url)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
