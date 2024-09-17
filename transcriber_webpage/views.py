import os
from django.shortcuts import render,HttpResponse
from dotenv import load_dotenv

load_dotenv()
# Create your views here.
def index(request):
    return render(request,'transcriber_webpage/home.html')

def test(request):
    return HttpResponse("Yeah test is working")

def get_api_key(request):
    api_key= os.getenv("DEEPGRAM_API_KEY")
    return HttpResponse(api_key)