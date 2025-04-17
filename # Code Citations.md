# Code Citations

## License: GPL_3_0
https://github.com/YikiNiya/ptu8_handmade_watercolors/tree/3c2ca9f3c2718dc657ef4d8d96370a0c01c05648/ptu8_handmade_watercolors/handmade_watercolors/views.py

```
=product_id)
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
```

