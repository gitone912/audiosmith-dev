from django.shortcuts import render,HttpResponse

# Create your views here.
def index(request):
    return render(request,'transcriber_webpage/home.html')

def test(request):
    return HttpResponse("Yeah test is working")
