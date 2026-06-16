(function () {
    function closeDropdowns(exceptMenu) {
        var menus = document.querySelectorAll('.dropdown-menu.show');
        Array.prototype.forEach.call(menus, function (menu) {
            if (menu !== exceptMenu) {
                menu.classList.remove('show');
            }
        });
    }

    document.addEventListener('click', function (event) {
        var collapseToggle = event.target.closest('[data-bs-toggle="collapse"]');
        var dropdownToggle = event.target.closest('[data-bs-toggle="dropdown"]');

        if (collapseToggle) {
            var targetSelector = collapseToggle.getAttribute('data-bs-target') || collapseToggle.getAttribute('href');
            var target = targetSelector ? document.querySelector(targetSelector) : null;

            if (target) {
                target.classList.toggle('show');
                collapseToggle.setAttribute('aria-expanded', target.classList.contains('show') ? 'true' : 'false');
            }
        }

        if (dropdownToggle) {
            event.preventDefault();
            var menu = dropdownToggle.parentElement ? dropdownToggle.parentElement.querySelector('.dropdown-menu') : null;

            if (menu) {
                var willOpen = !menu.classList.contains('show');
                closeDropdowns(menu);
                menu.classList.toggle('show', willOpen);
                dropdownToggle.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
            }
        } else if (!event.target.closest('.dropdown-menu')) {
            closeDropdowns(null);
        }
    });
})();
