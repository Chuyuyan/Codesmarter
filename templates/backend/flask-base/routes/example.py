from flask import Blueprint, request, jsonify
# {{ADDITIONAL_IMPORTS}}

example_bp = Blueprint('example', __name__, url_prefix='/api/example')

@example_bp.route('/', methods=['GET'])
def get_example():
    # {{CUSTOM_LOGIC}}
    return jsonify({'message': 'Example endpoint'})

@example_bp.route('/', methods=['POST'])
def create_example():
    data = request.get_json()
    # {{CUSTOM_LOGIC}}
    return jsonify({'message': 'Created', 'data': data}), 201

# {{CUSTOM_ROUTES}}

