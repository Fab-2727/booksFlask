const valueIsbn = document.getElementById("isbn").innerText;
const urlForReview = "{{ url_for('newReview', isbn=, v1=request.endpoint)}}";
const form = document.getElementById("review-user");

const isbn= valueIsbn.substring(6,valueIsbn.length);

let completeUrl = urlForReview.substring(0,29) + isbn + urlForReview.substring((29), urlForReview.length);
console.log(completeUrl);


form.action = completeUrl;