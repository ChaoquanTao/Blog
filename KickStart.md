---
title: KickStart
date: 2019-09-28 21:15:40
updated: 2019-09-28 21:15:40
tags:
categories:
---

```
import java.util.*;
    import java.io.*;
    public class Solution {
      public static void main(String[] args) {
        Scanner in = new Scanner(new BufferedReader(new InputStreamReader(System.in)));
        int t = in.nextInt(); // Scanner has functions to read ints, longs, strings, chars, etc.
        for (int i = 1; i <= t; ++i) {
          int n = in.nextInt();
          int m = in.nextInt();
          System.out.println("Case #" + i + ": " + (n + m) + " " + (n * m));
        }
      }
    }
```

