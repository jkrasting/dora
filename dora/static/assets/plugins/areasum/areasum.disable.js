function setOptions() {
      if ($("select[name=realm]").prop('value') == "Land") {
              $("input[id=plottype2][value=sum]").prop('disabled', false);
            } else {
                    $("input[id=plottype2][value=sum]").prop('disabled', true);
                    $("input[id=plottype1][value=average]").prop('checked', true);
            }};

  $('select[name="realm"]').change(function () {
        setOptions();
  });

    setOptions();
