---
title: Android学习笔记
date: 2018-07-04 15:46:41
categories: 移动开发
---



此文章谨用来记录我在做安卓过程中遇到的相关问题和知识点



### Handler

handler在创建之初，会和某个线程绑定，可以认为它是这个线程的代言人，其一个用途就是多线程通信，尤其是非线程安全情况下的线程通信



### Fragment

为什么会出现fragment这个东西呢，举个最简单的例子，就是想把一个安卓页面划分成多个部分，每个部分显示不同的内容，而这几个部分又属于同一个activity,比如我们使用qq或者微信的时候，地下有个导航栏，无论我们是选择哪一个，只有上面的部分在变，而导航栏却一直都在，这就是fragment的应用。

fragment英文叫做片段，顾名思义其实它就是activity的一个片段，一个子集，让一个activity占据整个页面很庞大，那我们就把activity分成好几个部分，让它们共享这个页面。

这里我拿一张google官方的示例图，就很能说明问题了。

![](https://ws1.sinaimg.cn/large/005UcYzagy1fvjqh9pivuj30fy09m3ze.jpg)



#### 生命周期

再甩一张官方图

![](https://ws1.sinaimg.cn/large/005UcYzagy1fvjqjfvz5fj307l0kvwgd.jpg)

上图表示在fragment所在的activity运行时fragment的生命周期

`添加Fragment`

有动态添加和静态添加两种方式，后面会讲到

`onAttach()`

该fragment被添加到activity中时被调用（两者建立关联时），且只会被调用一次

`onCreate()`

fragment被创建时调用

`onCreateView()`

绘制该fragment的view时被调用，且讲绘制的view返回

`onActivityCreate()`

fragment所在的activity启动完成后回调

`onStart()`

启动fragment时被回调

`onResume()`

恢复fragment时被调用，`onStart()`方法后一定回调`onResume()`



经过上述步骤，fragment就被激活了

`onPause()`

fragment被暂停时调用

`onStop()`

fragment停止时调用，停止并不意味着这个fragment被销毁，比如我们按下home键

`onDestroyView()`

销毁Fragment所包含的view

`onDestroy()`

销毁fragment

`onDetach()`

fragment被从activity中remove时调用



其实它的生命周期和activity很相似，理解它们的生命周期，这样就能更好的知道应该在它们的哪个阶段进行哪些操作。



#### 静/动态添加

上面提到，fragment是activity的片段，所以就有个这个片段何时被添加的问题。

无论动态添加还是静态添加，在此之前我们都要先定义好这个fragment的内部布局xml文件并且定义一个继承了Fragment的类和这个xml文件关联起来，有点类似于我们要定义好`listview`的每个item然后通过adapter将它们适配。

下面我们定义一个`chart_fragment`文件

```
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:id="@+id/textView"
        android:layout_width="wrap_content"
        android:layout_height="match_parent"
        android:layout_weight="1"
        android:text="this is chart fragment"
        android:textSize="20dp"/>
</LinearLayout>

```

然后用一个继承自Fragment的类将这个xml添加进来

```
 public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.chart_fragment,container,false);
    }
```

这样`ChartFragment`类就和我们的布局文件关联起来了，以后用`ChartFragment`就指的是这个fragment了



1. 静态添加

   直观讲就是在activity的布局文件中加入`fragment`标签

   ```
   <?xml version="1.0" encoding="utf-8"?>
   <LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
       android:orientation="horizontal"
       android:layout_width="match_parent"
       android:layout_height="match_parent">
       <fragment android:name="com.example.news.ArticleListFragment"
               android:id="@+id/list"
               android:layout_weight="1"
               android:layout_width="0dp"
               android:layout_height="match_parent" />
      
   </LinearLayout>
   ```

   像这样，可以发现上述fragment的name是一个类名，也就是我们上面关联的类名，这也是静态添加fragment的一个特点

2. 动态添加

   所谓动态添加就是我们不直接把fragment标签写死在activity的布局文件中，而是在activity布局文件中给fragment留一个container,比如各种layout,然后在代码中通过`FragmentSupportManager`来进行添加。我们获得Transaction对象，用它来操作fragment,比如add,remove,hide,show,replace等。

   ```
   getSupportFragmentManager().beginTransaction().replace(R.id.frame2,new MapFragment()).commit();
   ```


#### Fragment Activity交互

这里用菜鸟教程的一张图来说明问题

![](https://ws1.sinaimg.cn/large/005UcYzagy1fvjs01bp52j30p909840c.jpg)

这里面比较难理解的是Fragment向Activity传递数据，我个人是这样理解的：假设有这样一个场景，点击Fragment A中的某个选项需要切换到Fragment B,那么Fragment必须把这个讯息传给它所在的Activity,因为Fragment A是没有切换的能力的，这种大事必须A和B的爸爸来完成。那如何做呢？我们可以定义一个接口I，然后让Activity实现这个接口，这个接口里函数的参数就是Fragment A要向Activity传递的数据，然后我们在Fragment中获得Activity对象，调用这个接口函数，是不是就很巧妙的把Fragment A的信息（作为参数）传递给了Activity（Activity实现了这个接口，所以调用的时候自然能获得接口的参数，而这个参数来自于Fragment A）呢？

#### 遇到的问题

1. 我用的是两个fragment,一个静态添加一个动态添加，一个fragment中受到点击事件去动态添加另一个fragment时，总是失败，看完了网上的各种方法，如包的版本问题，support.v4还是app包,以及fragment的name问题，都没有找到原因，后来发现，原来是这个constraintlayout搞得我没有把fragment画出来，所以以后开发还是给布局加点颜色为好。
2. 我想在Activity中先模拟一次一个fragment中的点击事件，这样一进来屏幕就不会感觉很空洞，于是我在onCreate方法中添加了button的performclick方法，但是，没反应，又经过一阵搜寻，原来在onCreate中，其实fragment布局还没有加载完，这时候贸然performclick是没有作用的，应该讲方法加到onStart中，看来学好他们的生命周期还是很有用的鸭。



### 信号强度

1. 有两种信号单位，dbm和asu

asu(alone signal unit)：独立信号单元，是一种模拟信号。asu代表手机将它的位置传递给附近的信号塔的速率，它和dbm测量的是一样的东西，但是是以一种更加线性的方式来表示。

dBm：是一个表示功率绝对值的值（也可以认为是以1mW功率为基准的一个比值），计算公式为：10log（功率值/1mw）。 

2. 网络类型

   **电信**

   2G CDMA
   3G CDMA2000
   4G TD-LTE，FDD-LTE

   **移动**

   2G GSM
   3G TD-SCDMA
   4G TD-LTE，FDD-LTE

   **联通**

   2G GSM
   3G WCDMA
   4G TD-LTE，FDD-LTE

   **安卓api提供的类型**



### 权限管理

安卓的权限分正常权限和危险权限，正常权限在Manifest中添加一哈就可以了，但是危险权限自己添加后还需要一个手动申请并覆盖原来方法的过程。

通过`ActivityCompat.requestPermissions`来申请我们所需的权限，它会回调`onRequestPermissionsResult`方法，所以我们还需要复写这个方法来达到我们的目的，复写方式很简单，让`MainActivity`实现`ActivityCompat.OnRequestPermissionsResultCallback`接口（因为`onRequestPermissionsResult`方法就是i这个接口中的），然后再`MainActivity`中复写该方法即可



### Context 和 Activity 的关系

用一张图就很能说明问题了

![](https://ws1.sinaimg.cn/large/005UcYzaly1ftnlyzgz9gj30bp06674r.jpg)

#### 关于`findViewById`

刚刚在做一个`popupwindow`里面显示动态图表的东西,在找图表的id时总是返回空指针，后来发现，之前写的类里面总以为`findViewById`是Context的方法，所以此前在用这个方法的时候一直传递Context来调用，其实这是一个View的方法，虽然在同一个Context下，但已经是不同的视图了，所以总返回空指针。

### `setOnclickedListener`

在重写该接口的`onClicked`方法时，该方法的参数是被点击的那个视图，比如按钮等。



### `PopupWindow`

```
void showAtLocation (View parent, // 该属性只要是屏幕上任意控件对象即可
                int gravity, // 屏幕位置
                int x,  // 偏移坐标
                int y)
```

这里需要注意第一个参数是屏幕上的组件，但不能是`popupwindow`中的组建，否则会报错。


### Problems

1. AS视图编辑器里不能显示控件，最后解决办法，在style.xml中的parent=后面加Base.
2. 