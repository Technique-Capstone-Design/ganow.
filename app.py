import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# API 키 가져오기
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set the API_KEY environment variable.")

# Set up API with API key from environment variable
genai.configure(api_key=api_key)

# Sample data of furniture items with categories
furniture_items = [
    {"name": "Sofa A", "material": "Fabric", "price": 1200, "comfort": 8, "color": "Blue", "category": "sofa", "image": "images/sofa_a.jpg"},
    {"name": "Sofa B", "material": "Leather", "price": 1500, "comfort": 9, "color": "Brown", "category": "sofa", "image": "images/sofa_b.jpg"},
    {"name": "Chair A", "material": "Wood", "price": 300, "comfort": 6, "color": "Natural", "category": "chair", "image": "images/chair_a.jpg"},
    {"name": "Chair B", "material": "Metal", "price": 350, "comfort": 7, "color": "Black", "category": "chair", "image": "images/chair_b.jpg"}
]

@app.route('/')
def index():
    return render_template('index.html', items=furniture_items)

@app.route('/compare', methods=['POST'])
def compare():
    selected_items = request.form.getlist('items')
    comparison_data = [item for item in furniture_items if item['name'] in selected_items]
    
    categories = {item['category'] for item in comparison_data}
    if len(categories) > 1:
        return jsonify({"status": "error", "message": "선택한 항목들이 동일한 카테고리에 있어야 합니다."}), 400
    
    return jsonify({"status": "success", "html": render_template('compare.html', items=comparison_data, selected_items=selected_items)})

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    selected_items = request.form.getlist('items')
    if len(selected_items) != 2:
        return jsonify("Error: Please select exactly two items for comparison."), 400

    user_request = request.form.get('request_text', '')

    gagu_1 = next(item for item in furniture_items if item['name'] == selected_items[0])
    gagu_2 = next(item for item in furniture_items if item['name'] == selected_items[1])
    
    request_text = f"""
    다음 두 가구를 비교해 주세요:
    1. {gagu_1['name']}: 재질 - {gagu_1['material']}, 가격 - {gagu_1['price']}원, 편안함 - {gagu_1['comfort']}, 색상 - {gagu_1['color']}.
    2. {gagu_2['name']}: 재질 - {gagu_2['material']}, 가격 - {gagu_2['price']}원, 편안함 - {gagu_2['comfort']}, 색상 - {gagu_2['color']}.
    
    사용자 요청: {user_request}
    추천과 각 가구의 장단점을 *,# 사용 금지하고 제공해 주세요.
    """

    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(request_text)

        if not response or not hasattr(response, 'text'):
            return jsonify("Error: Failed to get a response from AI."), 500

        return jsonify(response.text.strip())
    except Exception as e:
        return jsonify(f"Error: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
