---
title: 【git篇】聊一聊git rebase和git checkout
categories: git
tag: git
---

### 前言

git作为日常开发中的必备工具，这篇文章主要介绍git的基本原理和一些常见的git使用场景。



### git 分区介绍

在 Git 中，有三个主要的区域：工作区（Working Directory）、暂存区（Staging Area）和仓库（Repository）。工作区是当前正在编辑和修改的项目目录。 暂存区是 Git 仓库中的一个临时存储区域，当我们执行 `git add` 命令时，工作区中的文件会添加到暂存区，暂存区也被叫做index。仓库是 Git 存储项目历史记录的地方，它是 Git 中最重要的部分。仓库保存了项目的每个版本、提交信息、分支、标签等。当执行 `git commit` 命令时，暂存区中的文件会被永久性地存储在仓库中，成为一个新的提交（commit）。

#### git中的HEAD指针

在 Git 中，`HEAD` 是一个特殊的指针，它指向当前所在的分支或提交，用于表示当前工作目录所处的状态，`HEAD`通常有两种指向：

1. `HEAD` 指向分支： 当我们位于某个分支上时，`HEAD` 指向该分支的最新提交。在这种情况下，`HEAD` 是一个符号引用，它指向该分支的最新提交的提交哈希值。
2. `HEAD` 指向提交： 当执行类似 `git checkout <commit_hash>` 的命令切换到特定提交时，`HEAD` 将指向该提交。这种情况下，`HEAD` 是一个直接指向提交的引用。需要注意的是，这种情况下，git会会处于头指针分离(head detached)状态，即`HEAD`不指向任何一个分支，而是指向一个提交，在这种情况下，如果重新修改代码并提交，它不会提交到任何一个已有的分支上，而是提交到了一个新的临时分支上。



### 常见git使用场景

#### 我想要开发新feature, 该怎么操作？

假设我们有三个分支：master, test和dev, 其中dev用于开发，test用于发布测试环境，master用于发布生产环境。当我们要开发新功能时，就需要从dev分支切出来一个新的分支进行操作，假设dev分支的提交记录如下，其中c3为最新一次提交：

![](http://cdn.inewbie.top/git/git-dev.png)

此时我们要从dev分支切出一个新分支来执行我们自己的操作:

```
git checkout -b feature/wuya
```

当我们在自己的分支上开发完并进行了一些提交后，想要合到dev，但是发现dev上已经合并了其他同学的一些提交:

![](http://cdn.inewbie.top/git/git-dev-and-feature.png)

此时要想将`feature/wuya`合到`dev`分支，有两种方法：

+ 第一种，直接git merge, 但是git merge默认是按照commit的时间排序的，这就意味着你的提交可能会被打散，比如下面这样：

![](http://cdn.inewbie.top/git/git-merge.png)

虽然也能用，但是由于自己的提交被打散到各个时间节点，不太美观 

+ 第二种，使用`git rebase`, 其作用就是把dev的提交压在自己的提交下面，当我们使用`git rebase dev`后，在进行pr, 那dev的提交将会是这样:

  ![](http://cdn.inewbie.top/git/git%20rebase.png)

  自己的提交整整齐齐地待在一起，看起来很舒服(其实git rebase的好处不仅在于看起来舒服， 当后续需要回滚等操作时，这种提交也会方便很多)。



#### 提PR时，发现自己有很多琐碎的无意义的commit, 该怎么操作？

压缩提交也是我们在日常开发中会用到的操作之一，尤其当开发的feature比较庞大时，可能不知不觉就提交了很多commit, 但是在发起代码PR时，最好将这些提交压缩合并一下，这样可以看起来更加简洁优雅。

其中一种压缩提交的方式就是使用 `git rebase -i HEAD~[N]`，其中N表示要压缩几条commit, 使用这条命令就可以进入`git rebase`的交互模式，我们会看到这样的界面

````
pick abc123 Commit message 1
pick def456 Commit message 2
pick ghi789 Commit message 3
````

通过使用`pick`或`squash`来决定哪条log要被留下，哪条log要被压缩，例如，如果你想将第二个和第三个提交压缩为一个提交，可以将第二个和第三个提交行的命令修改为 `squash`：

```
pick abc123 Commit message 1
squash def456 Commit message 2
squash ghi789 Commit message 3
```

这样操作后，当你再次使用`git log`查看时，会发现这三条commit被压缩成了一条，commit的log内容为“Commit message 1”.

除了使用向前数几条commit的方式之外，还可以使用`git rebase -i [commit-hash]`，只需要在-i后面输入具体的commit得哈希值即可。



#### 发现有几个文件做了不必要的修改，我应该如何撤回？

##### 方法一 使用`git checkout`

+ case 1: 当我们准备使用`git add .`提交代码时，我们对file.txt做了修改，在使用git add 时发现这些修改是不必要的，想撤回，那么可以使用

```
git checkout -- file.txt
```

> 当git checkout某个文件时，它会丢弃当前工作区指定文件的修改，并使用最近一次commit的内容来替换当前工作区的文件。

+ case 2: 如果我们已经通过`git add`将这些文件添加到了暂存区，那么可以先将 `file.txt` 从暂存区移除：

```
git reset HEAD file.txt
```

> 这个命令将会将 `file.txt` 从暂存区移除，但仍然保留修改的内容，然后使用`git checkout`撤销对 `file.txt` 的修改：

```
git checkout -- file.txt
```

> git reset <commit_hash>常见的有--soft, --mixed, --hard三个参数，默认为--mixed. 
>
> + --mixed表示reset之后会保留已修改的文件，但这些文件的状态是`unstaged`，即这些文件没有被执行git add
> + --soft表示reset之后会保留已修改的文件，但这些文件的状态是`to be commited`,即这些文件已经被`git add`了
> + --hard表示reset后不会保留已修改的文件，它会清空工作区内目标`commit`之后的所有修改



##### 方法二 使用`git restore`

`git restore` 是 Git 2.23 版本引入的一个命令，用于撤销对工作目录中文件的更改或恢复文件。它可以用来还原文件的内容或撤销暂存的更改，用法如下：

1. 当修改还没有使用`git add`添加到暂存区时，可以使用

   ```
   git restore <file>
   ```

   此命令会将指定文件的内容还原为最近一次提交时的状态，丢弃在工作目录中对该文件的修改。

2. 当修改已经使用`git add`添加到暂存区时，可以使用：

   ```
   git restore --staged <file>
   ```

   撤销对文件的 `git add` 操作，将文件的暂存状态还原为最近一次提交时的状态。



#### 我想查看某个文件的历史提交，该怎么操作

##### 使用git checkout 查看历史提交

当前`git commit`有a, b, c三个提交，其中c是最近提交，现在我想查看b版本的内容， 可以使用 `git checkout` 将指定文件切换到目标版本 b：

```
git checkout <commit_b_hash> -- <file_path>
```

查看完之后，如果想返回之前的分支，如dev，可以使用

```
git checkout dev
```



#### 我想把某个文件回滚到之前的版本，该怎么操作？

##### 方法一 使用`git revert`

```
git revert <commit_hash> -- <file_path>
```

上述命令会撤销对应文件在对应`commit`上的修改，需要注意的是, `git revert`会创建一个新的撤销提交。`git revert`只会撤销指定commit的修改，其它commit不会受影响，比如当前有`commit` a->b->c->d, 其中d为最新`commit`，使用`git revert b` 后，新的`commit history`为a->b->c->d->b',  这个操作只会撤销b的修改，c的修改不会受影响。



##### 方法二 使用`git reset` 

使用 `git reset` 回退到指定版本

```
git reset <commit_hash>
```

这将会将当前分支回退到目标`commit`，但保留更改的文件在工作区中的状态。

> `git revert <commit_hash>`只会回指定`commit`的内容，不会对该`commit`后面的其他`commit`有影响，但是
>
> `git reset <commit_hash>` 会将提交记录回滚到指定`commit`,意味着该`commit`后面的所有`commit`都会消失。



> 可以看到，`git checkout <commit_hash>`和`git reset <commit_hash>`都可以回退到指定的提交版本，但是两者有一定区别。简单来讲，`git checkout <commit_hash>`只会移动`HEAD`指针，分支本身是没有变化的，而`git reset <commit_hash>`不仅移动`HEAD`指针，分支本身也会被改变。所以，如果是想回退某个分支、修改后并重新提交，可以使用`git reset <commit_hash>`;  `git checkout <commit_hash>`更推荐用来查看某个提交的内容，不建议用来进行修改和提交，因为它会处于头指针分离(head detached)状态，即`HEAD`不指向任何一个分支，而是指向一个提交，在这种情况下，如果重新修改代码并提交，它不会提交到任何一个已有的分支上，而是提交到了一个新的临时分支上。

