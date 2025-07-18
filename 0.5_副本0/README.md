# Chinese Name & Signature Generator

A web application that generates Chinese names and personalized handwritten signatures for foreign users, with cultural explanations.

## Features
- Generate Chinese names based on user's foreign name
- Create personalized handwritten signatures
- Download generated signatures
- Provide cultural explanations and references for the Chinese name
- English language interface

## Technical Stack
- Frontend: HTML, CSS, JavaScript, Tailwind CSS
- Backend: Python with FastAPI
- AI Integration: Silicon Flow API
- Signature Generation: AI text-to-image model

## Setup Instructions
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Run the application: `uvicorn main:app --reload`

## TODO List
### Project Setup
- [ ] Create project directory structure
- [ ] Set up virtual environment
- [ ] Create requirements.txt file
- [ ] Configure environment variables

### Backend Development
- [ ] Create FastAPI application structure
- [ ] Implement name generation API endpoint
- [ ] Implement signature generation API endpoint
- [ ] Set up Silicon Flow API client
- [ ] Create cultural explanation generation logic

### Frontend Development
- [ ] Create HTML structure for the main page
- [ ] Implement Tailwind CSS styling
- [ ] Add JavaScript for form handling
- [ ] Implement signature display component
- [ ] Add download functionality for signatures

### AI Integration
- [ ] Implement Chinese name generation using Qwen2.5-72B-Instruct
- [ ] Develop prompt engineering for cultural explanations
- [ ] Set up signature generation using text-to-image model

### Testing & Deployment
- [ ] Write unit tests for API endpoints
- [ ] Test name generation logic
- [ ] Verify signature download functionality
- [ ] Prepare deployment instructions