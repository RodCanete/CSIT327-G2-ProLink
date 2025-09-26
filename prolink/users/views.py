from django.shortcuts import render, redirect

def login(request):
	error = None
	if request.method == "POST":
		username = request.POST.get("username")
		password = request.POST.get("password")
		# Dummy authentication
		if username == "admin" and password == "password":
			return redirect("/")  # Redirect to home or dashboard
		else:
			error = "Invalid username or password."
	return render(request, "users/login.html", {"error": error})
