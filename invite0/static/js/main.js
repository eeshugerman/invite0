// navbar menu dropdown
document.addEventListener('DOMContentLoaded', function() {

  // Get all "navbar-burger" elements
  const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);

  // Check if there are any navbar burgers
  if ($navbarBurgers.length > 0) {

    // Add a click event on each of them
    $navbarBurgers.forEach( el => {
      el.addEventListener('click', () => {

        // Get the target from the "data-target" attribute
        const target = el.dataset.target;
        const $target = document.getElementById(target);

        // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
        el.classList.toggle('is-active');
        $target.classList.toggle('is-active');

      });
    });
  }

  var dropdown = document.querySelector('.dropdown');
  if(!!dropdown){
    dropdown.addEventListener('click', function(event) {
      event.stopPropagation();
      dropdown.classList.toggle('is-active');
      if(!!document.querySelector('.fa-angle-down')){
        document.querySelector('.fa-angle-down').classList.add('fa-angle-up');
        document.querySelector('.fa-angle-down').classList.remove('fa-angle-down');
      }else{
        document.querySelector('.fa-angle-up').classList.add('fa-angle-down');
        document.querySelector('.fa-angle-up').classList.remove('fa-angle-up');
      }
    });
  }
});

// flash message delete button and auto-dismiss
document.addEventListener('DOMContentLoaded', () => {
    (document.querySelectorAll('.notification .delete') || []).forEach(($delete) => {
        $notification = $delete.parentNode;

        function dismiss() { $notification.parentNode.removeChild($notification); }
        $delete.addEventListener('click', dismiss);

        autoDismissSeconds = 10
        setTimeout(dismiss, autoDismissSeconds * 1000)
    });
});
