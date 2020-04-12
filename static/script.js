const password = document.getElementById('pwd');
const checkbox = document.getElementById('check');

checkbox.addEventListener("click", function () {
    if (password.type === "password") {
        password.type = "text";
    } else {
        password.type = "password";
    }
});

/* Validate the confirmpassword */