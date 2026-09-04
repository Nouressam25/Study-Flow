setTimeout(function () {

    const flash = document.querySelector(".flash");

    if (flash) {

        flash.style.transition = "opacity .5s ease";

        flash.style.opacity = "0";

        setTimeout(function () {

            flash.remove();

        }, 500);

    }

}, 3000);