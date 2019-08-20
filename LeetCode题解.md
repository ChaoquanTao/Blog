---
title: leetcode题解
date: 2018-05-03 11:13:20
categories: LeetCode
---

###542.01 矩阵

+ 题目描述

  给定一个由 0 和 1 组成的矩阵，找出每个元素到最近的 0 的距离。

  两个相邻元素间的距离为 1 。

+ 题目分析

  + ![](https://ws1.sinaimg.cn/large/005UcYzaly1fqlmlb1779j30fb08zjrc.jpg)


  + 可用动态规划来求解，每个元素距离0最近的距离 =  该元素邻居距离0最近的距离 + 1

  + 为了从分利用内存空间，我们仍然用这个矩阵来表示距离

  + 为零的元素不用处理，如果某个元素的邻居有0，那么将该元素置为1（说明它到0的距离为1）

  + 将剩下的元素（也就是周围全是1的元素）置为无穷大，这个初始化意味着他们到零的距离为无穷大，需要在后面的动态规划中求解

  + 通过上述的处理，我们可以得到，这些无穷大的值其实都被数字1或者边界所包含，通过边界值可以更新无穷大的值

    ![](https://ws1.sinaimg.cn/large/005UcYzaly1fqlmngbhtgj30mi089t8n.jpg)

  + 对矩阵进行遍历，第一顺序横向遍历，当遇见值为无穷大的元素时，更新它的值为 邻居到0最近距离+1 和无穷大 本身值的较小者

    `matrix[i][j]=min(matrix[i-1][j]+1,matrix[i][j]) //如果该元素不是第一列`

    第一次遍历将会和该元素的左边元素和上边元素比较

    第二次遍历从最后一行最后一列开始遍历，将会和该元素的右边和下边元素进行比较

+ 代码

  ```
  import static java.lang.Math.min;

  public class Matrix2{
      public static void main(String[] args) {
          int[][] matrix =
                  //{{0,0,0}, {0,1,0}, {1,1,1}} ;
                  {   {0, 0, 1, 0, 1, 1, 1, 0, 1, 1},
                          {1, 1, 1, 1, 0, 1, 1, 1, 1, 1},
                          {1, 1, 1, 1, 1, 0, 0, 0, 1, 1},
                          {1, 0, 1, 0, 1, 1, 1, 0, 1, 1},
                          {0, 0, 1, 1, 1, 0, 1, 1, 1, 1},
                          {1, 0, 1, 1, 1, 1, 1, 1, 1, 1},
                          {1, 1, 1, 1, 0, 1, 0, 1, 0, 1},
                          {0, 1, 0, 0, 0, 1, 0, 0, 1, 1},
                          {1, 1, 1, 0, 1, 1, 0, 1, 0, 1},
                          {1, 0, 1, 1, 1, 0, 1, 1, 1, 0}};

          int [][] matrix2 ;
          matrix2 = updateMatrix(matrix) ;
          System.out.println("last");
          for(int i=0 ; i<matrix2.length; i++){
              for(int j=0; j<matrix2[0].length;j++){
                  System.out.print(matrix2[i][j]+" ");
              }
              System.out.println();
          }

      }

      public static int[][] updateMatrix(int[][] matrix){
          //
          for(int i=0; i<matrix.length;i++){
              for(int j=0; j<matrix[0].length;j++){
                  if(matrix[i][j]==1){
                      if(i>0 && matrix[i-1][j]==0) {
                          matrix[i][j]=1;
                          continue;
                      }
                      if(i<matrix.length-1 && matrix[i+1][j]==0){
                          matrix[i][j]=1 ;
                          continue;
                      }
                      if(j>0 && matrix[i][j-1]==0){
                          matrix[i][j]=1 ;
                          continue;
                      }
                      if(j<matrix[0].length-1 && matrix[i][j+1]==0){
                          matrix[i][j]=1;
                          continue;
                      }
                      matrix[i][j]=65535 ;
                  }
              }
          }
          System.out.println("first ");
          for(int i=0 ; i<matrix.length; i++){
              for(int j=0; j<matrix[0].length;j++){
                  System.out.printf("%-8d",matrix[i][j]);
              }
              System.out.println();
          }

          for(int i=0; i<matrix.length;i++){
              for(int j=0; j<matrix[0].length;j++){
                  if(matrix[i][j]==65535){
                      if(i>0){
                          matrix[i][j] = min(matrix[i-1][j]+1,matrix[i][j]);
                      }
                      if(j>0){
                          matrix[i][j] = min(matrix[i][j-1]+1,matrix[i][j]);
                      }
                  }
              }
          }

          System.out.println("second ");
          for(int i=0 ; i<matrix.length; i++){
              for(int j=0; j<matrix[0].length;j++){
                  System.out.printf(matrix[i][j]+"\t");
              }
              System.out.println();
          }
          for(int i=matrix.length-1; i>=0;i--){
              for(int j=matrix[0].length-1;j>=0;j--){
                  if(i<matrix.length-1)
                      matrix[i][j]=min(matrix[i+1][j]+1,matrix[i][j]);
                  if(j<matrix[0].length-1)
                      matrix[i][j]=min(matrix[i][j+1]+1,matrix[i][j]);
              }
          }
    
          return matrix;
    
      }
  }
  ```

+ 关于疑问

  可能有人会想，为什么要遍历两遍，而不是在第一次遍历时就直接和前后左右邻居相比较，继续![](https://ws1.sinaimg.cn/large/005UcYzaly1fqlmngbhtgj30mi089t8n.jpg)看这张图，按照我们的思路处理后是这样的

  ![](https://ws1.sinaimg.cn/large/005UcYzaly1fqlmpv2zvcj30bi088wec.jpg)

  请看第一行倒数第二个元素`m[0][8]`，如果只进行一次顺序遍历，由于它底下的值`m[1][8]`没有更新，它将会认为从左边得到的4(`m[0][7]+1`)这个值是最小值，但是事实是，当它底下这个无穷大值如果经过更新成2，那么它的4也应该更新为3。如果按照我们只遍历一次的思想，它是等不到`m[1][8]`更新的，但是如果我们先正向遍历比较左边和上边元素，得到下图

  ![](https://ws1.sinaimg.cn/large/005UcYzaly1fqlmy9tk8sj30ba089t8k.jpg)

  第二次反向遍历时，当`m[0][8]`和它下面的`m[1][8]`比较时，因为`m[1][8]`已经更新，所以它也会被更新。

  所以说，第一波遍历时本来就是从左到右从上到下的顺序，即使强行和当前元素的右边和下边比较，因为这两边还没有更新，所以并没有什么效果，所以才需要两次遍历，且方向相反
  ```

  ```

### 456. 132模式

+ 题目描述

  给定一个整数序列：a1, a2, ..., an，一个132模式的子序列 a**i**, a**j**, a**k** 被定义为：当 **i** < **j** < **k** 时，a**i** < a**k** < a**j**。设计一个算法，当给定有 n 个数字的序列时，验证这个序列中是否含有132模式的子序列。

  **注意：**n 的值小于15000。

+ 分析

  最暴力的方法就是通过三重循环直接判断，但是运行时会超时，这里对三重循环进行优化，通过观察可知，假设三个数依次是x,y,z.如果y<=x,这时可以直接用y来替代x，因为用一个更小的值来做x肯定是不会错的。同理，如果z>=y，我们就用z的值来更新y。需要注意的是下标的移动。

+ 代码

  ```
  public boolean find132pattern(int[] nums) {
          int x,y,z ;
          int min,max ;
          if(nums.length==0)
              return false;
          min=max=nums[0] ;
          for(int i=1; i<nums.length;i++){
              min = nums[i]<min ? nums[i] : min ;
              max = nums[i]>max ? nums[i]:max ;
          }
          if(max-min<2)
              return false ;

          for(int i=0; i<nums.length;){
              x= nums[i];
              for(int j=i+1; j<nums.length;){
                  y=nums[j];
                  //如果遇见比x还小的值，就更新x,同时更新下标
                  if(y<=x){
                      x=y;
                      i=j;
                      j++;
                      continue ;
                  }

                  for(int k=j+1; k<nums.length;k++){
                      z=nums[k];
                      //如果遇见比y还大的值，就更新y,同时更新下标
                      if(z>=y){
                          y=z ;
                          j=k;
                          continue;
                      }
                      if( x>=z){
                          continue;
                      }
                      else
                          return true ;
                  }
                  j++;
              }
              i++;
          }
          return false ;
      }
  ```

+ 反思

  看了下里面大神解答，时间复杂度控制在O(n)也是可以解决这个问题的。先找到当前元素nums[i]前面所有元素中最小的元素min[i]，然后反向遍历，并在遍历时将元素加入集合，然后判断集合中是否存在大于当前元素nums[i]前面的最小元素min[i]的元素，如果存在且这个元素小于当前元素，则返回true.否则直到遍历结束并返回false.

### 650.2 Keys Keyboard

+ 题目描述

  Initially on a notepad only one character 'A' is present. You can perform two operations on this notepad for each step:

  1. `Copy All`: You can copy all the characters present on the notepad (partial copy is not allowed).
  2. `Paste`: You can paste the characters which are copied **last time**.

  Given a number `n`. You have to get **exactly** `n` 'A' on the notepad by performing the minimum number of steps permitted. Output the minimum number of steps to get `n` 'A'.

+ 题目分析

  题目最终化简为n的素数分解，然后将质因数求和

+ 代码

  ```
   public int minSteps(int n) {
          int sum=0;
          if(n==1)
              return 0 ;
          if(n==2)
              return 2;
          for(int i=2; i*i<=n;i++){
              while(n%i==0){
                  sum+=i ;
                  n/=i;
              }
          }
          if(n!=1)
              sum+=n;
         return sum ;
      }
  ```

  ​