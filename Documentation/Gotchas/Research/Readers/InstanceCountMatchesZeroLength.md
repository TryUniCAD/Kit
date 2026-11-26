# An integer count can appear to match zero length

A SOLIDWORKS feature pattern stores its count as an integer. Reading those same bytes as a floating-point length can produce a tiny value within display tolerance of zero. On the turbine wheel, the count of 11 at offset 38918 appeared as a candidate for the zero dimension in sketch 319.

Once independent controls, the keyword count, and the strict reader’s count span verify the integer field, the dimension audit excludes that location from floating-point matches. The report retains the excluded offset. The remaining scalar at offset 266936 matches the public sketch dimension span.
