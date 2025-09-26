document.addEventListener('DOMContentLoaded', function() {
	var form = document.getElementById('login-form');
	if (form) {
		form.addEventListener('submit', function(e) {
			var username = document.getElementById('username').value;
			var password = document.getElementById('password').value;
			if (!username || !password) {
				e.preventDefault();
				alert('Please enter both username and password.');
			}
		});
	}
});
