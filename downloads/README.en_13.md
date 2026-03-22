<!DOCTYPE html>
<html lang='zh-CN'>
<head>
<script>
  // 立即应用主题，避免页面闪烁 (FOUC)
  (function() {
    function getCookieTheme() {
      var match = document.cookie.match(/theme=(light|dark|system)/);
      return match ? match[1] : null;
    }
  
    function getCurrentTheme() {
      var cookieTheme = getCookieTheme();
      var savedTheme = localStorage.getItem('theme');
  
      // 优先使用 cookie 中的 theme
      if (cookieTheme) {
        // 如果 localStorage 里没有，就补回去
        if (!savedTheme) {
          localStorage.setItem('theme', cookieTheme);
        }
        return cookieTheme;
      }
  
      // 如果 cookie 中没有 theme，则使用 localStorage 中的 theme
      savedTheme = savedTheme && ['light', 'dark', 'system'].includes(savedTheme) ? savedTheme : 'system'; // 默认跟随系统
  
      return savedTheme;
    }
  
    var savedTheme = getCurrentTheme();
  
    // 检测系统是否为暗黑模式
    function isSystemDarkMode() {
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
  
    if (savedTheme === 'system') {
      // 系统模式：移除覆盖类，让CSS媒体查询自动处理
      document.documentElement.classList.remove('dark-mode-override');
      document.documentElement.classList.remove('dark-mode');
    } else {
      // 手动模式：添加覆盖类，禁用媒体查询
      document.documentElement.classList.add('dark-mode-override');
  
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-mode');
      } else {
        document.documentElement.classList.remove('dark-mode');
      }
    }
  })();
</script>

<title>README.en.md · openGauss/openGauss-server - Gitee</title>
<meta content='on' http-equiv='x-dns-prefetch-control'>
<link href='//e.gitee.com' rel='dns-prefetch'>
<link href='//files.gitee.com' rel='dns-prefetch'>
<link href='//toscode.gitee.com' rel='dns-prefetch'>
<link href='https://cn-assets.gitee.com' rel='dns-prefetch'>
<link rel="shortcut icon" type="image/vnd.microsoft.icon" href="https://cn-assets.gitee.com/assets/favicon-9007bd527d8a7851c8330e783151df58.ico" />
<link rel="canonical" href="https://gitee.com/opengauss/openGauss-server" />
<meta content='gitee.com/opengauss/openGauss-server git https://gitee.com/opengauss/openGauss-server.git' name='go-import'>
<meta charset='utf-8'>
<meta content='always' name='referrer'>
<meta content='Gitee' property='og:site_name'>
<meta content='Object' property='og:type'>
<meta content='https://gitee.com/opengauss/openGauss-server/blob/master/README.en.md' property='og:url'>
<meta content='https://gitee.com/static/images/logo_themecolor_circle.png' itemprop='image' property='og:image'>
<meta content='README.en.md · openGauss/openGauss-server - Gitee' itemprop='name' property='og:title'>
<meta content='openGauss kernel ~ openGauss is an open source relational database management system.' property='og:description'>
<meta content='码云,Gitee,代码托管,Git,Git@OSC,Gitee.com,开源,内源,项目管理,版本控制,开源代码,代码分享,项目协作,开源项目托管,免费代码托管,Git代码托管,Git托管服务' name='Keywords'>
<meta content='openGauss kernel ~ openGauss is an open source relational database management system.' itemprop='description' name='Description'>
<meta content='pc,mobile' name='applicable-device'>

<meta content="IE=edge" http-equiv="X-UA-Compatible" />
<meta name="csrf-param" content="authenticity_token" />
<meta name="csrf-token" content="l2HZSNbGojx0Lc8DoA6p76DmDyPVdLfHalVBn+MXCxhUudkRAIQiPOUproAMuobNhl/lgqCqCb9ltwOfKBxS0Q==" />

<link rel="stylesheet" media="all" href="https://cn-assets.gitee.com/assets/application-a90576fa5e179fe0fe375e8789eed5da.css" />
<script>
//<![CDATA[
window.gon = {};gon.locale="en";gon.sentry_dsn=null;gon.baidu_register_hm_push=null;gon.info={"controller_path":"blob","action_name":"show","current_user":false};gon.tour_env={"current_user":null,"action_name":"show","original_url":"https://gitee.com/opengauss/openGauss-server/blob/master/README.en.md","controller_path":"blob"};gon.http_clone="https://gitee.com/opengauss/openGauss-server.git";gon.user_project="opengauss/openGauss-server";gon.manage_branch="Manage branch";gon.manage_tag="Manage tag";gon.enterprise_id=5961634;gon.create_reaction_path="/opengauss/openGauss-server/reactions";gon.ipipe_base_url="https://go-api.gitee.com";gon.artifact_base_url="https://go-repo.gitee.com";gon.gitee_go_remote_url="https://go.gitee.com/assets";gon.gitee_go_active=true;gon.current_project_is_mirror=false;gon.show_repo_comment=false;gon.diagram_viewer_path="https://diagram-viewer.giteeusercontent.com";gon.ent_host="e.gitee.com";gon.ref="master";
//]]>
</script>
<script src="https://cn-assets.gitee.com/assets/application-ad1f81a78bdbda72def5fb7f8f77a8d1.js"></script>
<script src="https://cn-assets.gitee.com/assets/lib/jquery.timeago.en-d8a06c79c6bf9e7618c1ade936096da5.js"></script>

<link rel="stylesheet" media="all" href="https://cn-assets.gitee.com/assets/projects/application-46b94c31ba11ae8c37eacce2bdb5603e.css" />
<script src="https://cn-assets.gitee.com/assets/projects/app-2f2173bc0337df4edc569318c9a06dc6.js"></script>

<script type='text/x-mathjax-config'>
MathJax.Hub.Config({
  tex2jax: {
    inlineMath: [['$','$'], ['\\(','\\)']],
    displayMath: [["$$","$$"],["\\[","\\]"]],
    processEscapes: true,
    skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
    ignoreClass: "container|files",
    processClass: "markdown-body"
  }
});
</script>
<script src="https://cn-assets.gitee.com/uploads/resources/MathJax-2.7.2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>

<script>
  (function () {
    var messages = {
      'zh-CN': {
        addResult: '增加 <b>{term}</b>',
        count: '已选择 {count}',
        maxSelections: '最多 {maxCount} 个选择',
        noResults: '未找到结果',
        serverError: '连接服务器时发生错误'
      },
      'zh-TW': {
        addResult: '增加 <b>{term}</b>',
        count: '已選擇 {count}',
        maxSelections: '最多 {maxCount} 個選擇',
        noResults: '未找到結果',
        serverError: '連接服務器時發生錯誤'
      }
    }
  
    if (messages[gon.locale]) {
      $.fn.dropdown.settings.message = messages[gon.locale]
    }
  }());
</script>

<script>
  var userAgent = navigator.userAgent;
  var isLessIE11 = userAgent.indexOf('compatible') > -1 && userAgent.indexOf('MSIE') > -1;
  if(isLessIE11){
    var can_access = ""
    if (can_access != "true"){
      window.location.href = "/incompatible.html";
    }
  }
  document.addEventListener("error", function (ev) {
    var elem = ev.target;
    if (elem.tagName.toLowerCase() === 'img') {
      elem.src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAAAAACIM/FCAAACh0lEQVR4Ae3ch5W0OgyG4dt/mQJ2xgQPzJoM1m3AbALrxzrf28FzsoP0HykJEEAAAUQTBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEkKK0789+GK/I2ezfQB522PnS1qc8pGgXvr4tE4aY0XOUWlGImThWgyCk6DleixzE7qwBkg/MGiDPlVVAyp1VQGrPKiACDhFI6VkF5LmzCki+sg7IwDoglnVAil0IMkeG9CyUiwsxLFUVFzJJOQaKCjFCDN9RXMjIX7W6ztZXZDKKCyn8sWJvH+nca7WHDN9lROlAliPH9iRKCPI4cswFJQWxB46toLQgQ9jhn5QYZA9DOkoMUoQde5YapAxDWkoNYsOQR3KQd9CxUnIQF4S49CB9ENKlBxmDEKsFUgMCCCCAAHIrSF61f6153Ajy8nyiPr8L5MXnmm4CyT2fzN4DUvHZ+ntA2tOQBRBAAAEEEEAAAQQQ7ZBaC6TwSiDUaYHQ2yuB0MN+ft+43whyrs4rgVCjBUKTFshLC6TUAjGA3AxSaYFYLZBOC2RUAsk8h5qTg9QcbEoOsoQhQ2qQhsO5xCD5dgB5JQaZ+KBKGtKecvR81Ic0ZDjByKdDx0rSEDZ/djQbH+bkIdvfJFm98BfV8hD2zprfVdlu9PxVeyYAkciREohRAplJCaRSAplJCcQogTjSAdlyHRBvSAekJR0QRzogA+mADJkOiCPSAPEtqYBshlRAXC43hxix2QiOuEZkVERykGyNo9idIZKE0HO7XrG6OiMShlDWjstVzdPgXtUH9v0CEidAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQAABBBBAAAEEEEAAAQQQQP4HgjZxTpdEii0AAAAASUVORK5CYII=";
    }
  }, true);
</script>
</head>

<script src="//res.wx.qq.com/open/js/jweixin-1.2.0.js"></script>
<script>
  var title = document.title.replace(/( - Gitee| - 码云)$/, '')
      imgUrl = '';
  
  document.addEventListener('DOMContentLoaded', function(event) {
    var imgUrlEl = document.querySelector('.readme-box .markdown-body > img, .readme-box .markdown-body :not(a) > img');
    imgUrl = imgUrlEl && imgUrlEl.getAttribute('src');
  
    if (!imgUrl) {
      imgUrlEl = document.querySelector('meta[itemprop=image]');
      imgUrl = imgUrlEl && imgUrlEl.getAttribute('content');
      imgUrl = imgUrl || "https://gitee.com/static/images/logo_themecolor_circle.png";
    }
  
    wx.config({
      debug: false,
      appId: "wxff219d611a159737",
      timestamp: "1774149802",
      nonceStr: "6cf9ab5b58c9eb518a8a39bac58011e7",
      signature: "cce4cd56cf634e8a67e37bc3e7a9a2f3d212e66f",
      jsApiList: [
        'onMenuShareTimeline',
        'onMenuShareAppMessage'
      ]
    });
  
    wx.ready(function () {
      wx.onMenuShareTimeline({
        title: title, // 分享标题
        link: "https://gitee.com/opengauss/openGauss-server/blob/master/README.en.md", // 分享链接，该链接域名或路径必须与当前页面对应的公众号JS安全域名一致
        imgUrl: imgUrl // 分享图标
      });
      wx.onMenuShareAppMessage({
        title: title, // 分享标题
        link: "https://gitee.com/opengauss/openGauss-server/blob/master/README.en.md", // 分享链接，该链接域名或路径必须与当前页面对应的公众号JS安全域名一致
        desc: document.querySelector('meta[name=Description]').getAttribute('content'),
        imgUrl: imgUrl // 分享图标
      });
    });
    wx.error(function(res){
      console.error('err', res)
    });
  })
</script>

<body class='blob-site-content blob_show git-project lang-en'>
<header class='common-header fixed noborder' id='git-header-nav'>
<div class='ui container'>
<div class='ui menu header-menu header-container'>
<div class='git-nav-expand-bar'>
<i class='iconfont icon-mode-table'></i>
</div>
<div class='gitee-nav__sidebar'>
<div class='gitee-nav__sidebar-container'>
<div class='gitee-nav__sidebar-top'>
<div class='gitee-nav__avatar-box'></div>
<div class='gitee-nav__buttons-box'>
<a class="ui button small fluid orange" href="/login">Sign in</a>
<a class="ui button small fluid basic is-register" href="/signup">Sign up</a>
</div>
</div>
<div class='gitee-nav__sidebar-middle'>
<div class='gitee-nav__sidebar-list'>
<ul>
<li class='gitee-nav__sidebar-item'>
<a href="/explore"><i class='iconfont icon-ic-discover'></i>
<span class='gitee-nav__sidebar-name'>Explore</span>
</a></li>
<li class='gitee-nav__sidebar-item'>
<a href="/enterprises"><i class='iconfont icon-ic-enterprise'></i>
<span class='gitee-nav__sidebar-name'>Enterprise</span>
</a></li>
<li class='gitee-nav__sidebar-item'>
<a href="/education"><i class='iconfont icon-ic-education'></i>
<span class='gitee-nav__sidebar-name'>Education</span>
</a></li>
<li class='gitee-nav__sidebar-item split-line'></li>
<li class='gitee-nav__sidebar-item'>
<a href="/search"><i class='iconfont icon-ic-search'></i>
<span class='gitee-nav__sidebar-name'>Search</span>
</a></li>
<li class='gitee-nav__sidebar-item'>
<a href="/help"><i class='iconfont icon-help-circle'></i>
<span class='gitee-nav__sidebar-name'>Help</span>
</a></li>
<li class='gitee-nav__sidebar-item'>
<a href="/terms"><i class='iconfont icon-file'></i>
<span class='gitee-nav__sidebar-name'>Terms of use</span>
</a></li>
<li class='gitee-nav__sidebar-item'>
<a href="/about_us"><i class='iconfont icon-issuepx'></i>
<span class='gitee-nav__sidebar-name'>About Us</span>
</a></li>
</ul>
</div>
</div>
<div class='gitee-nav__sidebar-bottom'>
<div class='gitee-nav__sidebar-close-button'>
<i class='fa fa-angle-double-left'></i>
</div>
</div>
</div>
</div>

<!-- /todo 10周年活动结束后 恢复 -->
<div class='item gitosc-logo'>
<a href="https://gitee.com"><img alt='Gitee — A Git-based Code Hosting and Research Collaboration Platform' class='ui inline image light-mode-img' height='28' src='/static/images/logo-black.svg?t=158106664' title='Gitee — A Git-based Code Hosting and Research Collaboration Platform' width='95'>
<img alt='Gitee — A Git-based Code Hosting and Research Collaboration Platform' class='ui inline image dark-mode-img' height='28' src='/static/images/logo.svg?t=158106664' title='Gitee — A Git-based Code Hosting and Research Collaboration Platform' width='95'>
</a></div>
<a title="Explore" class="item " href="/explore">Explore
</a><a title="Enterprise" class="item " href="/enterprises">Enterprise
</a><a title="Education" class="item " href="/education">Education
</a><a title="Gitee Premium" class="item" target="_blank" href="https://gitee.cn?utm_source=giteecom">Gitee Premium
</a><a title="Gitee AI" class="item" id="gitee-blog" target="_blank" href="https://moark.com/serverless-api/?utm_sources=site_nav"><span>
Gitee AI
</span>
<img alt='Gitee AI' class='ui inline image' src='/static/images/notification-star.svg' style='transform: translate(-4.6px, -8.8px)' title='Gitee AI'>
</a><a title="AI teammates" class="item" id="gitee-ai-bot" target="_blank" href="https://gitee.com/ai-teammates"><span>AI teammates</span>
</a><div class='center responsive-logo'>
<a href="https://gitee.com"><img alt='Gitee — A Git-based Code Hosting and Research Collaboration Platform' class='ui inline image' height='24' src='/static/images/logo.svg?t=158106664' title='Gitee — A Git-based Code Hosting and Research Collaboration Platform' width='85'>
<img alt='Gitee — A Git-based Code Hosting and Research Collaboration Platform' class='ui inline black image' height='24' src='/static/images/logo-black.svg?t=158106664' title='Gitee — A Git-based Code Hosting and Research Collaboration Platform' width='85'>
</a></div>
<div class='right menu userbar right-header' id='git-nav-user-bar'>
<form class="ui item" id="navbar-search-form" data-text-require="Search keywords can not be less than one" data-text-filter="Invalid search content" data-text-search-site-projects="Search %{query} related projects site-wide" action="/search" accept-charset="UTF-8" method="get"><input name="utf8" type="hidden" value="&#x2713;" />
<input type="hidden" name="type" id="navbar-search-type" />
<input type="hidden" name="fork_filter" id="fork_filter" value="on" />
<div class='ui search header-search' style='position: relative;'>
<input type="text" name="q" id="navbar-search-input" value="" class="prompt" placeholder="Search" style="width: 100%; padding-right: 32px; box-sizing: border-box;" />
<span class='iconify' data-icon='gitee:search' style='position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-size: 16px; color:rgba(0, 0, 0, 0.88); pointer-events: none;'></span>
</div>
</form>

<script>
  var can_search_in_repo = 1,
      repo = "VFZSQmQwOUVaM3BQVkU1b1RucFplbHBuUFQxaE56WXpaZz09YTc2M2Y=",
      reponame = "opengauss/openGauss-server";
  
  $(function() {
    var $search = $('#navbar-search-form .ui.search');
    var $form = $('#navbar-search-form');
    var searchSiteProjectsText = $form.data('text-search-site-projects');
  
    $form.on('submit', function(e) {
      e.preventDefault(); // 防止默认提交
      var query = $('#navbar-search-input').val();
      if (query) {
        window.location = '/search?fork_filter=on&q=' + encodeURIComponent(query);
      }
    });
  
    // 原有的搜索逻辑保持不变
    $search.search({
      apiSettings: {
        url: '/search/relative_project?q=' + encodeURIComponent('{query}'),
        onResponse: function (res) {
          if (res && res.status === 200 && res.data) {
            var query = htmlSafe($search.search('get value'));
  
            res.data.map(function (item) {
              item.path_ns = '/' + item.path_ns;
              item.icon = 'iconfont icon-project-public';
            });
            res.data.unshift({
              name_ns: searchSiteProjectsText.replace('%{query}', "<b class='hl'>" + query + "</b>"),
              path_ns: '/search?fork_filter=on&q=' + encodeURIComponent(query),
              icon: 'iconfont icon-search'
            });
            return res;
          } else {
            return { data: [] };
          }
        }
      },
      fields: {
        results: 'data',
        description: 'name_ns',
        url: 'path_ns',
      },
      minCharacters: 1,
      maxResults: 10,
      searchDelay: 250,
      showNoResults: false,
      transition: 'fade'
    });
  });
</script>

<script src="https://cn-assets.gitee.com/webpacks/gitee_icons-c083090a7801eb0b2ce7.bundle.js"></script>
<script src="https://cn-assets.gitee.com/assets/theme_toggle-0c8215e3e0cd891c42ea4226ae882bfb.js"></script>
<link rel="stylesheet" media="screen" href="https://cn-assets.gitee.com/assets/fonts/font-awesome-febf886370cf750ab95af17cede1d51f.css" />
<a class="item git-nav-user__login-item" href="/login">Sign in
</a><a class="item git-nav-user__register-item" href="/signup">Sign up
</a><script>
  $('.destroy-user-session').on('click', function() {
    localStorage.setItem('theme', 'system');
    $.cookie('access_token', null, { path: '/' });
  })
</script>

</div>
</div>
</div>
</header>
<script>
  Gitee.initNavbar()
  Gitee.initRepoRemoteWay()
  $.cookie('user_locale',null)
</script>

<script>
  var userAgent = navigator.userAgent;
  var isLessIE11 = userAgent.indexOf('compatible') > -1 && userAgent.indexOf('MSIE') > -1;
  if(isLessIE11){
    var can_access = ""
    if (can_access != "true"){
      window.location.href = "/incompatible.html";
    }
  }
</script>

<div class='fixed-notice-infos'>
<div class='all-messages'>
</div>
<div class='ui container'>
<div class='flash-messages' id='messages-container'></div>
</div>
<script>
  (function() {
    $(function() {
      var $error_box, alertTip, notify_content, notify_options, template;
      template = '<div data-notify="container" class="ui {0} message" role="alert">' + '<i data-notify="dismiss" class="close icon"></i>' + '<span data-notify="message">{2}</span>' + '</div>';
      notify_content = null;
      notify_options = {};
      alertTip = '';
      $error_box = $(".flash_error.flash_error_box");
      if (notify_options.type === 'error' && $error_box.length > 0 && !$.isEmptyObject(notify_content.message)) {
        if (notify_content.message === 'captcha_fail') {
          alertTip = "The captcha is incorrect";
        } else if (notify_content.message === 'captcha_expired') {
          alertTip = "The captcha was expired, please refresh it";
        } else if (notify_content.message === 'not_found_in_database') {
          alertTip = "Invalid email or password.";
        } else if (notify_content.message === 'not_found_and_show_captcha') {
          alertTip = "Invalid email or password.";
        } else if (notify_content.message === 'phone_captcha_fail') {
          alertTip = "The phone captcha is incorrect";
        } else {
          alertTip = notify_content.message;
        }
        return $error_box.html(alertTip).show();
      } else if (notify_content) {
        if ("show" === 'third_party_binding') {
          return $('#third_party_binding-message').html(notify_content.message).addClass('ui message red');
        }
        notify_options.delay = 3000;
        notify_options.template = template;
        notify_options.offset = {
          x: 10,
          y: 30
        };
        notify_options.element = '#messages-container';
        return $.notify(notify_content, notify_options);
      }
    });
  
  }).call(this);
</script>

</div>
<script>
  (function() {
    $(function() {
      var setCookie;
      setCookie = function(name, value) {
        $.cookie(name, value, {
          path: '/',
          expires: 365
        });
      };
      $('#remove-bulletin, #remove-bulletin-dashboard').on('click', function() {
        setCookie('remove_bulletin', "gitee-maintain-1774101652");
        $('#git-bulletin').hide();
      });
      $('#remove-member-bulletin').on('click', function() {
        setCookie('remove_member_bulletin', "gitee_member_bulletin");
        $(this).parent().hide();
      });
      return $('#remove-gift-bulletin').on('click', function() {
        setCookie('remove_gift_bulletin', "gitee-gift-bulletin");
        $(this).parent().hide();
      });
    });
  
  }).call(this);
</script>
<script>
  function closeMessageBanner(pthis, type, val) {
    var json = {}
  
    val = typeof val === 'undefined' ? null : val
    $(pthis).parent().remove()
    if (type === 'out_of_enterprise_member') {
      json = {type: type, data: val}
    } else if (type === 'enterprise_overdue') {
      json = {type: type, data: val}
    }
    $.post('/profile/close_flash_tip', json)
  }
</script>

<div class='project_detail site-content'>
<div class='git-project-header'>
<div class='fixed-notice-infos'>
<div class='ui info icon floating message green' id='fetch-ok' style='display: none'>
<div class='content'>
<div class='header status-title'>
<i class='info icon status-icon'></i>
Fetch the repository succeeded.
</div>
</div>
</div>
<div class='ui info icon floating message error' id='fetch-error' style='display: none'>
<div class='content'>
<div class='header status-title'>
<i class='info icon status-icon'></i>
<span class='error_msg'></span>
</div>
</div>
</div>
</div>
<div class='ui container'>
<div class='git-project-categories'>
<a href="/explore">Open Source</a>
<span class='symbol'>></span>
<a href="/explore/database-related">Database Related</a>
<span class='symbol'>&gt;</span>
<a href="/explore/database-service">Database Service</a>
<span class='symbol and-symbol'>&&</span>
</div>

<div class='git-project-header-details'>
<div class='git-project-header-container'>
<div class='git-project-header-actions'>
<div class='ui tiny modal project-donate-modal' id='project-donate-modal'>
<i class='iconfont icon-close close'></i>
<div class='header'>Donate</div>
<div class='content'>
Please sign in before you donate.
</div>
<div class='actions'>
<a class='ui blank button cancel'>Cancel</a>
<a class='ui orange ok button' href='/login'>Sign in</a>
</div>
</div>
<div class='ui small modal wepay-qrcode'>
<i class='iconfont icon-close close'></i>
<div class='header'>
Scan WeChat QR to Pay
<span class='wepay-cash'></span>
</div>
<div class='content weqcode-center'>
<img id='wepay-qrcode' src=''>
</div>
<div class='actions'>
<div class='ui cancel blank button'>Cancel</div>
<div class='ui ok orange button'>Complete</div>
</div>
</div>
<div class='ui mini modal' id='confirm-alipay-modal'>
<div class='header'>Prompt</div>
<div class='content'>
Switch to Alipay.
</div>
<div class='actions'>
<div class='ui approve orange button'>OK</div>
<div class='ui blank cancel button'>Cancel</div>
</div>
</div>

<div class='tootip no-arrow' data-position='bottom center' data-tooltip='试试让马建仓 AI 助手来解读仓库吧～'>
<div class='chat-button'>
<a target="_blank" class="d-align-center" href="https://chat.gitee.com?repo_owner=opengauss&amp;repo_path=openGauss-server"><img alt="richgiteeai" style="width:14px; height:14px;" src="https://cn-assets.gitee.com/assets/rich_giteeai-78477b2d4703c69031f90ac6a524c3e3.svg" />
</a></div>
</div>
<span class='ui buttons basic watch-container'>
<div class='ui dropdown button js-project-watch' data-watch-type='unwatch'>
<input type='hidden' value=''>
<i class='iconfont icon-watch'></i>
<div class='text'>
Watch
</div>
<i class='dropdown icon'></i>
<div class='menu'>
<a data-value="unwatch" class="item" rel="nofollow" data-method="post" href="/opengauss/openGauss-server/unwatch"><i class='iconfont icon-msg-read'></i>
Unwatch
</a><a data-value="watching" class="item" rel="nofollow" data-method="post" href="/opengauss/openGauss-server/watch"><i class='iconfont icon-msg-read'></i>
Watching
</a><a data-value="releases_only" class="disabled item" rel="nofollow" data-method="post" href="/opengauss/openGauss-server/release_only_watch"><i class='iconfont icon-msg-read'></i>
Releases Only
</a><a data-value="ignoring" class="item" rel="nofollow" data-method="post" href="/opengauss/openGauss-server/ignoring_watch"><i class='iconfont icon-msg-read'></i>
Ignoring
</a></div>
</div>
<style>
  .js-project-watch .text .iconfont {
    display: none; }
  .js-project-watch a, .js-project-watch a:hover {
    color: #000; }
  .js-project-watch .item > .iconfont {
    visibility: hidden;
    margin-left: -10px; }
  .js-project-watch .selected .iconfont {
    visibility: visible; }
  .js-project-watch .menu {
    margin-top: 4px !important; }
</style>
<script>
  $('.js-project-watch').dropdown({
    action: 'select',
    onChange: function(value, text, $selectedItem) {
      var type = value === 'unwatch' ? 'Watch' : 'Watching';
      $(this).children('.text').text(type);
      $(this).dropdown('set selected', value)
    }
  });
</script>

<a class="ui button action-social-count" title="444" href="/opengauss/openGauss-server/watchers">444
</a></span>
<span class='basic buttons star-container ui'>
<a class="ui button star" href="/login"><i class='iconfont icon-star'></i>
Star
</a><a class="ui button action-social-count " title="1493" href="/opengauss/openGauss-server/stargazers">1.5K
</a></span>
<span class='ui basic buttons fork-container' title='You do not have the permission to fork this repository'>
<a class="ui button fork" title="You must be signed in to fork a repository" href="/login"><i class='iconfont icon-fork'></i>
Fork
</a><a class="ui button action-social-count disabled-style" title="1813" href="/opengauss/openGauss-server/members">1.8K
</a></span>
</div>
<h2 class='git-project-title mt-0 mb-0'>
<span class="project-title"><a href='/opengaussorg' class='mr-05'><i class="iconfont icon-enterprise-badge" title="This is an enterprise's repository"></i></a> <i class="project-icon iconfont icon-project-public" style='margin-right: 4px' title="This is a public repository"></i> <a title="openGauss" class="author" href="/opengauss">openGauss</a>/<a title="openGauss-server" class="repository" target="" style="padding-bottom: 0px; margin-right: 4px" href="/opengauss/openGauss-server">openGauss-server</a></span><span class="project-badges"><style>
  .gitee-modal {
    width: 500px !important; }
</style>
</span>
<input type="hidden" name="project_title" id="project_title" value="openGauss/openGauss-server" />
</h2>
</div>
</div>
</div>
<script>
  var title_import_url = "false";
  var title_post_url = "/opengauss/openGauss-server/update_import";
  var title_fork_url = "/opengauss/openGauss-server/sync_fork";
  var title_project_path = "openGauss-server";
  var title_p_name = "openGauss-server";
  var title_p_id= "10088393";
  var title_description = "openGauss kernel ~ openGauss is an open source relational database management system.";
  var title_form_authenticity_token = "5/Q1IKaGkC2thv7lffYkVou9Z4pC/jTXYbvhdDatYUwkLDV5cMQQLTyCn2bRQgt0rQSNKzcgiq9uWaN0/aY4hQ==";
  var watch_type = "unwatch";
  var checkFirst = false;
  
  $('.js-project-watch').dropdown('set selected', watch_type);
  $('.checkbox.sync-wiki').checkbox();
  $('.checkbox.sync-prune').checkbox();
  $('.checkbox.team-member-checkbox').checkbox();
  $('.project-closed-label').popup({ 
    popup: '.project-closed-popup', 
    position: 'top center', 
    hoverable: true,
  });
</script>
<style>
  i.loading, .icon-sync.loading {
    -webkit-animation: icon-loading 1.2s linear infinite;
    animation: icon-loading 1.2s linear infinite;
  }
  .qrcode_cs {
    float: left;
  }
  .check-sync-wiki {
    float: left;
    height: 28px;
    line-height: 28px;
  }
  .sync-wiki-warn {
    color: #e28560;
  }
</style>

<div class='git-project-nav'>
<div class='ui container'>
<div class='ui secondary pointing menu'>
<a class="item active " href="/opengauss/openGauss-server"><i class='iconfont icon-code'></i>
Code
</a><a class="item " href="/opengauss/openGauss-server/issues"><i class='iconfont icon-task'></i>
Issues
<span class='ui mini circular label'>
980
</span>
</a><a class="item " href="/opengauss/openGauss-server/pulls"><i class='iconfont icon-pull-request'></i>
Pull Requests
<span class='ui mini circular label'>
152
</span>
</a><a class="item " href="/opengauss/openGauss-server/wikis"><i class='iconfont icon-wiki'></i>
Wiki
</a><a class="item  " href="/opengauss/openGauss-server/graph/master"><i class='iconfont icon-statistics'></i>
Insights
</a><a class="item " href="/opengauss/openGauss-server/gitee_go"><i class='iconfont icon-workflow'></i>
Pipelines
</a><div class='item'>
<div class='ui pointing top right dropdown git-project-service'>
<div>
<i class='iconfont icon-service'></i>
Service
<i class='dropdown icon'></i>
</div>
<div class='menu' style='display:none'>
<a class="item" href="/opengauss/openGauss-server/quality_analyses?platform=sonar_qube"><img src="https://cn-assets.gitee.com/assets/sonar_mini-5e1b54bb9f6c951d97fb778ef623afea.png" alt="Sonar mini" />
<div class='item-title'>
Quality Analysis
</div>
</a><a class="item" target="_blank" href="https://gitee.com/help/articles/4193"><img src="https://cn-assets.gitee.com/assets/jenkins_for_gitee-554ec65c490d0f1f18de632c48acc4e7.png" alt="Jenkins for gitee" />
<div class='item-title'>
Jenkins for Gitee
</div>
</a><a class="item" target="_blank" href="https://gitee.com/help/articles/4318"><img src="https://cn-assets.gitee.com/assets/cloudbase-1197b95ea3398aff1df7fe17c65a6d42.png?20200925" alt="Cloudbase" />
<div class='item-title'>
Tencent CloudBase
</div>
</a><a class="item" target="_blank" href="https://gitee.com/help/articles/4330"><img src="https://cn-assets.gitee.com/assets/cloud_serverless-686cf926ced5d6d2f1d6e606d270b81e.png" alt="Cloud serverless" />
<div class='item-title'>
Tencent Cloud Serverless
</div>
</a><a class="item" href="/opengauss/openGauss-server/open_sca"><img src="https://cn-assets.gitee.com/assets/open_sca/logo-9049ced662b2f9936b8001e6f9cc4952.png" alt="Logo" />
<div class='item-title'>
悬镜安全
</div>
</a><a class="item" target="_blank" href="https://help.gitee.com/devops/connect/Aliyun-SAE"><img src="https://cn-assets.gitee.com/assets/SAE-f3aa9366a1e2b7fff4747402eb8f10c3.png" alt="Sae" />
<div class='item-title'>
Aliyun SAE
</div>
</a><a class="item" id="update-codeblitz-link" target="_blank" href="https://gitee.com/link?target=https%3A%2F%2Fcodeblitz.cloud.alipay.com%2Fgitee%2Fopengauss%2FopenGauss-server%2Ftree%2Fmaster%2FREADME.en.md"><img style="width:100px;margin-top:4px" src="https://cn-assets.gitee.com/assets/Codeblitz-8824e38875a106e16e29ff57ec977b08.png" alt="Codeblitz" />
<div class='item-title'>
Codeblitz
</div>
</a><a class="item" id="update-codeblitz-link" target="_blank" href="/opengauss/openGauss-server/sbom"><img style="width:30px;margin-top:4px" src="https://cn-assets.gitee.com/assets/SBOM-36dbd3141411c5c1e9095e8d1d21baf0.png" alt="Sbom" />
<div class='item-title'>
SBOM
</div>
</a><button class='ui orange basic button quit-button' id='quiting-button'>
Don’t show this again
</button>
</div>
</div>
</div>
</div>
</div>
</div>
<script>
  $('.git-project-nav .ui.dropdown').dropdown({ action: 'nothing' });
  // 下线小红点 var gitee_reward_config = JSON.parse(localStorage.getItem('gitee_reward_config') || null) ||  true
  var gitee_reward_config = true
  var $settingText = $('.setting-text')
  // 如果没有访问过
  if(!gitee_reward_config) $settingText.addClass('red-dot')
  $('.git-project-service').dropdown({
    on: 'click',
    action: 'nothing',
    onShow: function () {
      const branch = 'master'
      let newUrl = `https://codeblitz.cloud.alipay.com/gitee/opengauss/openGauss-server/tree/`
      const url = decodeURIComponent(window.location.pathname);
      const startIndex = url.indexOf('master');
      if (startIndex !== -1) {
        newUrl = newUrl + url.substring(startIndex); // 从分支名开始截取
      }else{
        newUrl = newUrl + branch
      }
      const linkElement = document.getElementById("update-codeblitz-link");
      linkElement.setAttribute("href", window.location.origin + "/link?target=" + encodeURIComponent(newUrl));
    },
  })
</script>
<style>
  .git-project-nav i.checkmark.icon {
    color: green;
  }
  #quiting-button {
    display: none;
  }
  
  .git-project-nav .dropdown .menu.hidden:after {
    visibility: hidden !important;
  }
</style>
<script>
  isSignIn = false
  isClickGuide = false
  $('#git-versions.dropdown').dropdown();
  $.ajax({
    url:"/opengauss/openGauss-server/access/add_access_log",
    type:"GET"
  });
  $('#quiting-button').on('click',function() {
    $('.git-project-service').click();
    if (isSignIn) {
      $.post("/projects/set_service_guide")
    }
    $.cookie("Serve_State", true, { expires: 3650, path: '/'})
    $('#quiting-button').hide();
  });
  if (!(isClickGuide || $.cookie("Serve_State") == 'true')) {
    $('.git-project-service').click()
    $('#quiting-button').show()
  }
</script>

</div>
<div class='ui container'>
<div class='register-guide'>
<div class='register-container'>
<div class='regist'>
Create your Gitee Account
</div>
<div class='description'>
Explore and code with more than 14 million developers，Free private repositories ！：）
</div>
<a class="ui orange button free-registion" href="/signup?from=project-guide">Sign up</a>
<div class='login'>
Already have an account?
<a href="/login?from=project-guide">Sign in</a>
</div>
</div>
</div>

<script defer='defer' src='/static/javascripts/file-icons.js'></script>
<div class='git-project-content-wrapper'>

<div class='ui grid blob-ddd' id='project-wrapper'>
<div class='project-left-side-contaner wide column left-side' id='project-left-side-contaner'>
<link href='/webpacks/osc-element-ui-theme/index.css' rel='stylesheet' type='text/css'>
<div class='left-side-container' style='height: 100%'>
<div class='d-flex-between'>
<div class='d-align-center' id='left-head_root_file'>
<div class='file-iconify-item' onclick="$('.project-left-side-contaner').hide();$('#file-iconify-wrapper').removeClass('hide').addClass('d-align-center')">
<span class='iconify' data-icon='gitee:sidebar-expand' style='font-size: 16px;'></span>
</div>
<span class='text-bold'>文件</span>
</div>
<div class='ml-1' id='left-head_root_actions' style='flex: 1'>
<div class='ui horizontal list repo-action-list d-flex d-align-center repo-action-list-right'>
<div class='item search-box-container'>
<div class='ui icon input search-input' id='search-box'>
<input class='search-file-name' maxlength='40' placeholder='Search' type='text'>
</div>
<a class='d-flex d-align-center head-search-file-btn' id='search-file-btn'>
<span class='iconify' data-icon='gitee:search' style='font-size: 16px;color:#979CAC;margin-right:10px'></span>
</a>
<div class='filter-file-container' style='display: none;'></div>
</div>
<script>
  (function() {
    const $dropdown = $('#git-tree-file[data-id="project_tree"]');
    const dropdownEl = $dropdown[0];
    const $plusBox = $dropdown.closest('.plus-box');
    const dropdownAppendToBody = false;
    let allowHide = true;
  
    if (dropdownAppendToBody) {
      document.body.addEventListener('click', function(e) {
        allowHide = true;
        let current = e.target;
        while (current !== null) {
          if (current === dropdownEl) {
            allowHide = false;
            break;
          }
          current = current.parentElement;
        }
        if (allowHide) $dropdown.dropdown('hide');
      }, true);
    }
  
    $dropdown.dropdown({
      action: 'hide',
      onHide: function () {
        $plusBox.removeClass('click-active');
  
        return allowHide;
      },
      onShow: function () {
        $plusBox.addClass('click-active');
  
        if (!dropdownAppendToBody) return;
        const $wrapper = this.$menuWrapper || $('<div class="ui top dropdown active visible"></div>');
        const offset = $(this).offset();
        $wrapper.css({
          position: 'absolute',
          top: offset.top,
          left: offset.left,
          marginTop: '1rem',
          zIndex: 1000
        });
  
        if (this.loaded) return;
  
        // destroy prev dropdown
        document.querySelectorAll('.ui.dropdown[data-prev-dropdown]').forEach(function(el) {
          el.parentNode.removeChild(el);
        });
        const $menu = $(this).find('.menu');
        $menu.css({
          display: 'block',
          border: '1px solid rgba(34,36,38,0.15)',
          borderRadius: '4px',
          boxShadow: '0px 2px 3px 0px rgba(34, 36, 38, 0.15)'
        });
        // 移动到 body
        $wrapper.append($menu);
        $wrapper.appendTo('body');
        $wrapper.attr('data-prev-dropdown', '');
        this.$menuWrapper = $wrapper;
        this.loaded = true;
      }
    });
  })();
  
  $('#git-project-root-actions #git-tree-file').on('click', function() {
    $('#git-project-root-actions .plus-box').addClass('click-active')
    $('#git-project-root-actions .repo-dropdown-box').addClass('transition visible')
  })
  
  $('.disabled-upload-readonly').popup({
    content: "Readonly directory does not allow uploading files",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-create-folder').popup({
    content: "Readonly directory does not allow directory creation",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-create-file').popup({
    content: "Readonly directory does not allow files creation",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-create-submodule').popup({
    content: "Readonly directory does not allow submodule creation",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-upload-readonly, .disabled-create-folder, .disabled-create-file, .disabled-create-submodule').click(function() {
    return false
  })
</script>
<style>
  .disabled-upload-readonly, .disabled-create-file, .disabled-create-folder, .disabled-create-submodule {
    background-color: #dcddde !important;
    color: rgba(0, 0, 0, 0.4) !important;
    opacity: 0.3 !important;
    background-image: none !important;
    -webkit-box-shadow: none !important;
            box-shadow: none !important; }
</style>

<div class='item compare-box' data-content='Compare view'>
<a class="ui d-flex d-align-center webide" target="_blank" href="/opengauss/openGauss-server/compare/master...master"><span class='iconify' data-icon='gitee:diff' style='font-size: 16px;color:#979CAC;margin-right:12px'></span>
</a></div>
</div>
<script>
  $('.webIDE-box').popup()
  $('.compare-box').popup()
</script>
<script src="https://cn-assets.gitee.com/assets/file_search/app-21e8df8af6aa09b8995390509269205b.js"></script>
<style>
  .filter-file-container-hide {
    display: none !important; }
</style>

</div>
</div>
<div class='left-project-branch-item git-project-branch-item'>
<input type="hidden" name="path" id="path" value="README.en.md" />
<div class='ui top left pointing dropdown gradient button dropdown-has-tabs' id='git-project-branch'>
<input type="hidden" name="ref" id="ref" value="master" />
<div class='default text'>
master
</div>
<i class='dropdown icon'></i>
<div class='menu'>
<div class='ui left icon input'>
<span class='dropdown-search-icon iconify' data-icon='gitee:search' style='font-size: 14px;'></span>
<input class='search-branch' placeholder='Search branch' type='text'>
</div>
<div class='tab-menu project-branch-tab-menu d-flex'>
<div class='tab-menu-item' data-placeholder='Search branches' data-tab='branches'>
Branches (20)
</div>
<div class='tab-menu-item' data-placeholder='Search tags' data-tab='tags'>
Tags (32)
</div>
<div class='d-align-center' style='flex:1;justify-content:end;'>
<div class='tab-menu-action' data-tab='branches'>
<a class="ui link button" href="/opengauss/openGauss-server/branches">Manage</a>
</div>
<div class='tab-menu-action' data-tab='tags'>
<a class="ui link button" href="/opengauss/openGauss-server/tags">Manage</a>
</div>
</div>
</div>
<div class='tab scrolling menu' data-tab='branches' id='branches_panel'>
<div data-value="master" class="item" title="master"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>master</span></div>
<div data-value="6.0.0" class="item" title="6.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>6.0.0</span></div>
<div data-value="3.0.0" class="item" title="3.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>3.0.0</span></div>
<div data-value="5.0.0" class="item" title="5.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>5.0.0</span></div>
<div data-value="feature_1230_4" class="item" title="feature_1230_4"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>feature_1230_4</span></div>
<div data-value="datavec_poc" class="item" title="datavec_poc"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>datavec_poc</span></div>
<div data-value="tp_poc" class="item" title="tp_poc"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>tp_poc</span></div>
<div data-value="7.0.0-RC2" class="item" title="7.0.0-RC2"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>7.0.0-RC2</span></div>
<div data-value="7.0.0-RC1" class="item" title="7.0.0-RC1"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>7.0.0-RC1</span></div>
<div data-value="master_bak08271930" class="item" title="master_bak08271930"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>master_bak08271930</span></div>
<div data-value="iud_dev" class="item" title="iud_dev"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>iud_dev</span></div>
<div data-value="dev_board" class="item" title="dev_board"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>dev_board</span></div>
<div data-value="5.1.0" class="item" title="5.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>5.1.0</span></div>
<div data-value="kms" class="item" title="kms"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>kms</span></div>
<div data-value="2.0.0" class="item" title="2.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>2.0.0</span></div>
<div data-value="3.1.0" class="item" title="3.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>3.1.0</span></div>
<div data-value="2.1.0" class="item" title="2.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>2.1.0</span></div>
<div data-value="1.1.0" class="item" title="1.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.1.0</span></div>
<div data-value="1.0.1" class="item" title="1.0.1"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.0.1</span></div>
<div data-value="1.0.0" class="item" title="1.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.0.0</span></div>
</div>
<div class='tab scrolling menu' data-tab='tags' id='tags_panel'>
<div class='item' data-value='v6.0.3'>v6.0.3</div>
<div class='item' data-value='v5.0.5'>v5.0.5</div>
<div class='item' data-value='v7.0.0-RC2'>v7.0.0-RC2</div>
<div class='item' data-value='v6.0.2'>v6.0.2</div>
<div class='item' data-value='v7.0.0-RC1'>v7.0.0-RC1</div>
<div class='item' data-value='v6.0.1'>v6.0.1</div>
<div class='item' data-value='v3.0.6'>v3.0.6</div>
<div class='item' data-value='v6.0.0'>v6.0.0</div>
<div class='item' data-value='v3.0.5B009'>v3.0.5B009</div>
<div class='item' data-value='v5.0.3'>v5.0.3</div>
<div class='item' data-value='v5.0.2'>v5.0.2</div>
<div class='item' data-value='v6.0.0-RC1'>v6.0.0-RC1</div>
<div class='item' data-value='v3.0.5'>v3.0.5</div>
<div class='item' data-value='v5.0.1'>v5.0.1</div>
<div class='item' data-value='v5.1.0'>v5.1.0</div>
<div class='item' data-value='5.1.0'>5.1.0</div>
<div class='item' data-value='v5.0.0'>v5.0.0</div>
<div class='item' data-value='v3.0.3'>v3.0.3</div>
<div class='item' data-value='v3.1.1'>v3.1.1</div>
<div class='item' data-value='v3.0.2'>v3.0.2</div>
</div>
</div>
</div>
<style>
  .iconfont.icon-shieldlock {
    color: #8c92a4;
  }
  .dropdown-search-icon {
    position: absolute;
    top: 8px;
    left: 11px;
  }
</style>
<style>
  #git-project-branch .project-branch-tab-menu, .project-branch-item .project-branch-tab-menu {
    padding-left: 0px !important;
    padding-right: 0px !important;
    margin: 0 11px !important;
    border-bottom: 1px solid #dfe3e9 !important; }
  #git-project-branch .ui.dropdown .menu, .project-branch-item .ui.dropdown .menu {
    width: 360px !important; }
    #git-project-branch .ui.dropdown .menu .item, .project-branch-item .ui.dropdown .menu .item {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap; }
  #git-project-branch .tab-menu-actions, .project-branch-item .tab-menu-actions {
    position: absolute;
    right: 0px !important;
    bottom: 0.357em; }
  #git-project-branch .tab-menu-action, .project-branch-item .tab-menu-action {
    position: relative !important;
    right: 0px !important;
    bottom: 0px !important; }
  #git-project-branch .menu::after, .project-branch-item .menu::after {
    display: none !important; }
</style>
<script>
  var $branchesDropdown = $('#branches_panel');
  var $tagsDropdown = $('#tags_panel');
  var $searchNameInput = $('.search-branch');
  var concurrentRequestLock = false;
  var filterXSS = window.filterXSS;
  var search_text = "";
  var branch_page_number = 1;
  var branch_total_pager = Math.ceil(20 / 20) || 1
  
  var flag_is_loading = false;
  var flag_page_number = 1;
  var flag_total_pager = Math.ceil(32 / 20) || 1
  
  $branchesDropdown.scroll(function() {
    var branchesPanel = document.getElementById('branches_panel');
    var numOfBranches = $branchesDropdown.children().length;
    if (branchesPanel.clientHeight + branchesPanel.scrollTop + 37 > branchesPanel.scrollHeight && numOfBranches < 20) {
      debounceLoadMoreBranches.call();
    }
  });
  function resetFlagVal() {
    flag_is_loading = false;
    flag_page_number = 1;
    flag_total_pager = 1;
  
    concurrentRequestLock = false
    search_text = "";
    branch_page_number = 1;
    branch_total_pager = 1
  }
  $searchNameInput.on('input', window.globalUtils.debouce(function (e) {
    resetFlagVal()
    var $currentTab = $('.tab-menu-action.active');
    var numOfBranches = $branchesDropdown.children().length;
    var searchWord = $searchNameInput.val().trim();
    search_text = searchWord
    if($currentTab.data('tab') === 'branches') {
      if (searchWord !== "") {
        loadData(searchWord,1);
      } else {
        loadData();
      }
    }
    var numOfTags = $tagsDropdown.children().length;
    if($currentTab.data('tab') === 'tags') {
      if (searchWord !== "") {
        fetchTags(searchWord,1);
      } else {
        fetchTags();
      }
    }
  }, 500));
  
  function toggleNoResultView($popPanel) {
    let no_data_html= `<div class='mt-1 mb-1 d-flex-center'> <span>暂无数据</span> </div>`
    $popPanel.append(no_data_html)
  }
  var debounceLoadMoreBranches = window.globalUtils.debouce(function () {
    if (concurrentRequestLock) return;
    branch_page_number += 1;
    if (branch_page_number > branch_total_pager) return;
    loadData(search_text, branch_page_number);
  }, 350);
  
  function loadData(search, page) {
    if (concurrentRequestLock) { return; }
    concurrentRequestLock = true;
  
    var searchParams = search || "";
    var pageParams = page || 1;
    $.ajax({
      url: "/" + gon.user_project + "/branches/names.json",
      type: 'GET',
      data: {
        search: searchParams,
        page: pageParams,
      },
      dataType: 'json',
      success: function (data) {
        branch_total_pager = data.total_pages;
        var html = '';
  
        if (pageParams === 1) {
          $branchesDropdown.empty();
        }
        data.branches.forEach(function (branch) {
          var protectRule = '';
          var branchName = filterXSS(branch.name);
          var icon = 'gitee:branch'
          if(branch.branch_type.value === 1) {
            var rule = filterXSS(branch.protection_rule.wildcard);
            protectRule = `<i
                class="iconfont icon-shieldlock protected-branch-popup"
                data-title="受保护分支"
                data-content='保护规则： ${rule}'
              >
              </i>`
            icon ='gitee:pen-lock'
          }else if(branch.branch_type.value === 2) {
            icon ='gitee:pen-ban'
          }
          var branchIcon = `<span class="iconify" data-icon=${icon} style="font-size: 13px; margin-right:4px; color:#8C92A4"></span>`
          html += `<div data-value='${branchName}' class="item">
                    ${branchIcon} 
                    <span>${branchName}</span> ${protectRule}
                    </div>`
        });
        $branchesDropdown.append(html);
        $('.protected-branch-popup').popup()
        if (pageParams === 1 && data.count === 0) {
          toggleNoResultView($branchesDropdown);
        }
      },
      complete: function () {
        concurrentRequestLock = false;
      }
    });
  }
  
  
  
  $tagsDropdown.scroll(function() {
    var tagsPanel = document.getElementById('tags_panel');
    var numOfTags = $tagsDropdown.children().length;
    if (tagsPanel.clientHeight + tagsPanel.scrollTop + 37 > tagsPanel.scrollHeight && numOfTags < 32) {
      debounceLoadMore.call();
    }
  });
  var debounceLoadMore = window.globalUtils.debouce(function () {
    if (flag_is_loading) return;
    flag_page_number += 1;
    if (flag_page_number > flag_total_pager) return;
    fetchTags(search_text, flag_page_number);
  }, 350);
  
  function fetchTags(search, page) {
    var searchParams = search || "";
    var pageParams = page || 1;
  
    if (flag_is_loading) return;
    flag_is_loading = true;
  
    $.ajax({
      url: "/" + gon.user_project + "/tags/names.json",
      data: {
        search: searchParams,
        page: pageParams,
      },
      type: "GET",
      xhrFields: {
        withCredentials: true,
      },
      success: function (data) {
        flag_total_pager = data.total_pages;
        if (pageParams === 1) {
          $tagsDropdown.html('');
        }
        data.tags.forEach((tag) => {
          const itemDiv = document.createElement('div');
          itemDiv.classList.add('item');
          itemDiv.setAttribute('data-value', tag.name);
          itemDiv.innerText = window.filterXSS(tag.name);
          $tagsDropdown.append(itemDiv)
        });
        if (pageParams === 1 && data.count === 0) {
          toggleNoResultView($tagsDropdown);
        }
      },
      error: function () {
      },
      complete: function () {
        flag_is_loading = false;
      },
    });
  }
  $('.project-branch-tab-menu').on('click','.tab-menu-item', function (e) {
    var $currentTab = $(this).data('tab')
    if($currentTab === 'branches') {
      $searchNameInput.val('')
      search_text = '';
      loadData()
    }
    if($currentTab === 'tags') {
      $searchNameInput.val('')
      search_text = '';
      fetchTags();
    }
  })
</script>

<script>
  $(function () {
    var curNode = $('.git-project-branch-item')
    if (true ){
      curNode = $('.left-project-branch-item')
    }else {
      curNode = $('.git-project-branch-item')
    }
    Gitee.initTabsInDropdown(curNode.find('#git-project-branch').dropdown({
      fullTextSearch: true,
      selectOnKeydown: false,
      direction: 'downward',
      action: function (text,value,el) {
        var oItemOrInitObject = el[0] || el
        var isNotSelect = oItemOrInitObject.dataset.tab && oItemOrInitObject.dataset.tab === 'branches'
        if(isNotSelect){
          console.warn("You didn't choose a branch")
          return
        }
        var path = $('#path').val();
        var href = ['/opengauss/openGauss-server/tree', encodeURIComponent(value), path].join('/');
        window.location.href = href;
        return true
      },
      onNoResults: function (searchTerm) {
        //未找到结果
        return true
      },
    }));
    $('.protected-branch-popup').popup()
  })
</script>

</div>
<div data-init-path='README.en.md' data-repo-path='opengauss/openGauss-server' id='project-tree-container'></div>
</div>
<style>
  .left-side-container {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-orient: vertical;
    -webkit-box-direction: normal;
        -ms-flex-direction: column;
            flex-direction: column; }
    .left-side-container .file-iconify-item {
      display: -webkit-box;
      display: -ms-flexbox;
      display: flex;
      padding: 8px;
      border-radius: 4px;
      margin-right: 8px;
      width: 32px;
      height: 32px;
      text-align: center; }
      .left-side-container .file-iconify-item:hover {
        background-color: #f5f7fa; }
</style>
<script>
  if (!false && window.Gitee.setFullscreen){
    window.Gitee.setFullscreen(true);
  }else {
    window.Gitee.setFullscreen(false);
  }
</script>
<script src="https://cn-assets.gitee.com/webpacks/vendors_lib-7ff466a6da368d391eda.js" defer="defer"></script>
<script src="https://cn-assets.gitee.com/webpacks/project_tree-2d6f0e39ac0b8c1f63af.bundle.js" defer="defer"></script>

</div>
<div class='sixteen wide column right-wrapper' id='sixteen'>
<div class='git-project-content' id='git-project-content'>
<div class='row'>
<div class='git-project-desc-wrapper'>
<script>
  $('.git-project-desc-wrapper .ui.dropdown').dropdown();
  if (false) {
    gon.project_new_blob_path = "/opengauss/openGauss-server/new/master/README.en.md"
    bindShowModal({
      el: $('.no-license .project-license__create'),
      complete: function(data, modal) {
        if (!data.haveNoChoice && !data.data) {
          Flash.show('Please select an open source license')
        } else {
          location.href = gon.project_new_blob_path + '?license=' + data.data
        }
      },
      skip: function () {
        location.href = gon.project_new_blob_path + '?license'
      }
    });
  }
  
  $(".project-admin-action-box .reject").click(function() {
    var reason = $('[name=review-reject-reason]').val();
    if (!reason) {
      Flash.error('请选择不通过理由')
      return
    }
    $.ajax({
      type: 'POST',
      url: "/admin/shumei_content/shumei_check/reject_project_public",
      data: {
        reason: reason,
        status: 'rejected',
        project_id: 10088393
      },
      success: function(result){
        if(result.status == 'success'){
          window.location.reload();
        }else{
          Flash.error(result.message)
        }
      }
    })
  })
  
  $(".project-admin-action-box .approve").click(function(){
  
    $.ajax({
      type: 'POST',
      url: "/admin/shumei_content/shumei_check/reject_project_public",
      data: {
        status: 'approved',
        project_id: 10088393
      },
      success: function(result){
        if(result.status == 'success'){
          window.location.reload();
        }else{
          Flash.error(result.message)
        }
      }
    })
  })
  
  $(".project-admin-action-box .waiting").click(function(){
  
    $.ajax({
      type: 'POST',
      url: "/admin/shumei_content/shumei_check/reject_project_public",
      data: {
        status: 'waiting',
        project_id: 10088393
      },
      success: function(result){
        if(result.status == 'success'){
          window.location.reload();
        }else{
          Flash.error(result.message)
        }
      }
    })
  })
  
  $('i.help.circle.icon').popup({
    popup: '.no-license .ui.popup',
    position: 'right center'
  });
  
  $('#remove-no-license-message').on('click', function() {
    $.cookie("skip_repo_no_license_message_10088393", 'hide', { expires: 365 });
    $('#user-no-license-message').hide();
    return;
  });
</script>
</div>

</div>
<div class='git-project-bread' id='git-project-bread'>
<div class='ui horizontal list mr-1' id='git-branch-dropdown' style='display: none;'>
<div class='item git-project-branch-item'>
<input type="hidden" name="path" id="path" value="README.en.md" />
<div class='ui top left pointing dropdown gradient button dropdown-has-tabs' id='git-project-branch'>
<input type="hidden" name="ref" id="ref" value="master" />
<div class='default text'>
master
</div>
<i class='dropdown icon'></i>
<div class='menu'>
<div class='ui left icon input'>
<span class='dropdown-search-icon iconify' data-icon='gitee:search' style='font-size: 14px;'></span>
<input class='search-branch' placeholder='Search branch' type='text'>
</div>
<div class='tab-menu project-branch-tab-menu d-flex'>
<div class='tab-menu-item' data-placeholder='Search branches' data-tab='branches'>
Branches (20)
</div>
<div class='tab-menu-item' data-placeholder='Search tags' data-tab='tags'>
Tags (32)
</div>
<div class='d-align-center' style='flex:1;justify-content:end;'>
<div class='tab-menu-action' data-tab='branches'>
<a class="ui link button" href="/opengauss/openGauss-server/branches">Manage</a>
</div>
<div class='tab-menu-action' data-tab='tags'>
<a class="ui link button" href="/opengauss/openGauss-server/tags">Manage</a>
</div>
</div>
</div>
<div class='tab scrolling menu' data-tab='branches' id='branches_panel'>
<div data-value="master" class="item" title="master"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>master</span></div>
<div data-value="6.0.0" class="item" title="6.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>6.0.0</span></div>
<div data-value="3.0.0" class="item" title="3.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>3.0.0</span></div>
<div data-value="5.0.0" class="item" title="5.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>5.0.0</span></div>
<div data-value="feature_1230_4" class="item" title="feature_1230_4"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>feature_1230_4</span></div>
<div data-value="datavec_poc" class="item" title="datavec_poc"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>datavec_poc</span></div>
<div data-value="tp_poc" class="item" title="tp_poc"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>tp_poc</span></div>
<div data-value="7.0.0-RC2" class="item" title="7.0.0-RC2"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>7.0.0-RC2</span></div>
<div data-value="7.0.0-RC1" class="item" title="7.0.0-RC1"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>7.0.0-RC1</span></div>
<div data-value="master_bak08271930" class="item" title="master_bak08271930"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>master_bak08271930</span></div>
<div data-value="iud_dev" class="item" title="iud_dev"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>iud_dev</span></div>
<div data-value="dev_board" class="item" title="dev_board"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>dev_board</span></div>
<div data-value="5.1.0" class="item" title="5.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>5.1.0</span></div>
<div data-value="kms" class="item" title="kms"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>kms</span></div>
<div data-value="2.0.0" class="item" title="2.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>2.0.0</span></div>
<div data-value="3.1.0" class="item" title="3.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>3.1.0</span></div>
<div data-value="2.1.0" class="item" title="2.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>2.1.0</span></div>
<div data-value="1.1.0" class="item" title="1.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.1.0</span></div>
<div data-value="1.0.1" class="item" title="1.0.1"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.0.1</span></div>
<div data-value="1.0.0" class="item" title="1.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.0.0</span></div>
</div>
<div class='tab scrolling menu' data-tab='tags' id='tags_panel'>
<div class='item' data-value='v6.0.3'>v6.0.3</div>
<div class='item' data-value='v5.0.5'>v5.0.5</div>
<div class='item' data-value='v7.0.0-RC2'>v7.0.0-RC2</div>
<div class='item' data-value='v6.0.2'>v6.0.2</div>
<div class='item' data-value='v7.0.0-RC1'>v7.0.0-RC1</div>
<div class='item' data-value='v6.0.1'>v6.0.1</div>
<div class='item' data-value='v3.0.6'>v3.0.6</div>
<div class='item' data-value='v6.0.0'>v6.0.0</div>
<div class='item' data-value='v3.0.5B009'>v3.0.5B009</div>
<div class='item' data-value='v5.0.3'>v5.0.3</div>
<div class='item' data-value='v5.0.2'>v5.0.2</div>
<div class='item' data-value='v6.0.0-RC1'>v6.0.0-RC1</div>
<div class='item' data-value='v3.0.5'>v3.0.5</div>
<div class='item' data-value='v5.0.1'>v5.0.1</div>
<div class='item' data-value='v5.1.0'>v5.1.0</div>
<div class='item' data-value='5.1.0'>5.1.0</div>
<div class='item' data-value='v5.0.0'>v5.0.0</div>
<div class='item' data-value='v3.0.3'>v3.0.3</div>
<div class='item' data-value='v3.1.1'>v3.1.1</div>
<div class='item' data-value='v3.0.2'>v3.0.2</div>
</div>
</div>
</div>
<style>
  .iconfont.icon-shieldlock {
    color: #8c92a4;
  }
  .dropdown-search-icon {
    position: absolute;
    top: 8px;
    left: 11px;
  }
</style>
<style>
  #git-project-branch .project-branch-tab-menu, .project-branch-item .project-branch-tab-menu {
    padding-left: 0px !important;
    padding-right: 0px !important;
    margin: 0 11px !important;
    border-bottom: 1px solid #dfe3e9 !important; }
  #git-project-branch .ui.dropdown .menu, .project-branch-item .ui.dropdown .menu {
    width: 360px !important; }
    #git-project-branch .ui.dropdown .menu .item, .project-branch-item .ui.dropdown .menu .item {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap; }
  #git-project-branch .tab-menu-actions, .project-branch-item .tab-menu-actions {
    position: absolute;
    right: 0px !important;
    bottom: 0.357em; }
  #git-project-branch .tab-menu-action, .project-branch-item .tab-menu-action {
    position: relative !important;
    right: 0px !important;
    bottom: 0px !important; }
  #git-project-branch .menu::after, .project-branch-item .menu::after {
    display: none !important; }
</style>
<script>
  var $branchesDropdown = $('#branches_panel');
  var $tagsDropdown = $('#tags_panel');
  var $searchNameInput = $('.search-branch');
  var concurrentRequestLock = false;
  var filterXSS = window.filterXSS;
  var search_text = "";
  var branch_page_number = 1;
  var branch_total_pager = Math.ceil(20 / 20) || 1
  
  var flag_is_loading = false;
  var flag_page_number = 1;
  var flag_total_pager = Math.ceil(32 / 20) || 1
  
  $branchesDropdown.scroll(function() {
    var branchesPanel = document.getElementById('branches_panel');
    var numOfBranches = $branchesDropdown.children().length;
    if (branchesPanel.clientHeight + branchesPanel.scrollTop + 37 > branchesPanel.scrollHeight && numOfBranches < 20) {
      debounceLoadMoreBranches.call();
    }
  });
  function resetFlagVal() {
    flag_is_loading = false;
    flag_page_number = 1;
    flag_total_pager = 1;
  
    concurrentRequestLock = false
    search_text = "";
    branch_page_number = 1;
    branch_total_pager = 1
  }
  $searchNameInput.on('input', window.globalUtils.debouce(function (e) {
    resetFlagVal()
    var $currentTab = $('.tab-menu-action.active');
    var numOfBranches = $branchesDropdown.children().length;
    var searchWord = $searchNameInput.val().trim();
    search_text = searchWord
    if($currentTab.data('tab') === 'branches') {
      if (searchWord !== "") {
        loadData(searchWord,1);
      } else {
        loadData();
      }
    }
    var numOfTags = $tagsDropdown.children().length;
    if($currentTab.data('tab') === 'tags') {
      if (searchWord !== "") {
        fetchTags(searchWord,1);
      } else {
        fetchTags();
      }
    }
  }, 500));
  
  function toggleNoResultView($popPanel) {
    let no_data_html= `<div class='mt-1 mb-1 d-flex-center'> <span>暂无数据</span> </div>`
    $popPanel.append(no_data_html)
  }
  var debounceLoadMoreBranches = window.globalUtils.debouce(function () {
    if (concurrentRequestLock) return;
    branch_page_number += 1;
    if (branch_page_number > branch_total_pager) return;
    loadData(search_text, branch_page_number);
  }, 350);
  
  function loadData(search, page) {
    if (concurrentRequestLock) { return; }
    concurrentRequestLock = true;
  
    var searchParams = search || "";
    var pageParams = page || 1;
    $.ajax({
      url: "/" + gon.user_project + "/branches/names.json",
      type: 'GET',
      data: {
        search: searchParams,
        page: pageParams,
      },
      dataType: 'json',
      success: function (data) {
        branch_total_pager = data.total_pages;
        var html = '';
  
        if (pageParams === 1) {
          $branchesDropdown.empty();
        }
        data.branches.forEach(function (branch) {
          var protectRule = '';
          var branchName = filterXSS(branch.name);
          var icon = 'gitee:branch'
          if(branch.branch_type.value === 1) {
            var rule = filterXSS(branch.protection_rule.wildcard);
            protectRule = `<i
                class="iconfont icon-shieldlock protected-branch-popup"
                data-title="受保护分支"
                data-content='保护规则： ${rule}'
              >
              </i>`
            icon ='gitee:pen-lock'
          }else if(branch.branch_type.value === 2) {
            icon ='gitee:pen-ban'
          }
          var branchIcon = `<span class="iconify" data-icon=${icon} style="font-size: 13px; margin-right:4px; color:#8C92A4"></span>`
          html += `<div data-value='${branchName}' class="item">
                    ${branchIcon} 
                    <span>${branchName}</span> ${protectRule}
                    </div>`
        });
        $branchesDropdown.append(html);
        $('.protected-branch-popup').popup()
        if (pageParams === 1 && data.count === 0) {
          toggleNoResultView($branchesDropdown);
        }
      },
      complete: function () {
        concurrentRequestLock = false;
      }
    });
  }
  
  
  
  $tagsDropdown.scroll(function() {
    var tagsPanel = document.getElementById('tags_panel');
    var numOfTags = $tagsDropdown.children().length;
    if (tagsPanel.clientHeight + tagsPanel.scrollTop + 37 > tagsPanel.scrollHeight && numOfTags < 32) {
      debounceLoadMore.call();
    }
  });
  var debounceLoadMore = window.globalUtils.debouce(function () {
    if (flag_is_loading) return;
    flag_page_number += 1;
    if (flag_page_number > flag_total_pager) return;
    fetchTags(search_text, flag_page_number);
  }, 350);
  
  function fetchTags(search, page) {
    var searchParams = search || "";
    var pageParams = page || 1;
  
    if (flag_is_loading) return;
    flag_is_loading = true;
  
    $.ajax({
      url: "/" + gon.user_project + "/tags/names.json",
      data: {
        search: searchParams,
        page: pageParams,
      },
      type: "GET",
      xhrFields: {
        withCredentials: true,
      },
      success: function (data) {
        flag_total_pager = data.total_pages;
        if (pageParams === 1) {
          $tagsDropdown.html('');
        }
        data.tags.forEach((tag) => {
          const itemDiv = document.createElement('div');
          itemDiv.classList.add('item');
          itemDiv.setAttribute('data-value', tag.name);
          itemDiv.innerText = window.filterXSS(tag.name);
          $tagsDropdown.append(itemDiv)
        });
        if (pageParams === 1 && data.count === 0) {
          toggleNoResultView($tagsDropdown);
        }
      },
      error: function () {
      },
      complete: function () {
        flag_is_loading = false;
      },
    });
  }
  $('.project-branch-tab-menu').on('click','.tab-menu-item', function (e) {
    var $currentTab = $(this).data('tab')
    if($currentTab === 'branches') {
      $searchNameInput.val('')
      search_text = '';
      loadData()
    }
    if($currentTab === 'tags') {
      $searchNameInput.val('')
      search_text = '';
      fetchTags();
    }
  })
</script>

<script>
  $(function () {
    var curNode = $('.git-project-branch-item')
    if (true ){
      curNode = $('.left-project-branch-item')
    }else {
      curNode = $('.git-project-branch-item')
    }
    Gitee.initTabsInDropdown(curNode.find('#git-project-branch').dropdown({
      fullTextSearch: true,
      selectOnKeydown: false,
      direction: 'downward',
      action: function (text,value,el) {
        var oItemOrInitObject = el[0] || el
        var isNotSelect = oItemOrInitObject.dataset.tab && oItemOrInitObject.dataset.tab === 'branches'
        if(isNotSelect){
          console.warn("You didn't choose a branch")
          return
        }
        var path = $('#path').val();
        var href = ['/opengauss/openGauss-server/tree', encodeURIComponent(value), path].join('/');
        window.location.href = href;
        return true
      },
      onNoResults: function (searchTerm) {
        //未找到结果
        return true
      },
    }));
    $('.protected-branch-popup').popup()
  })
</script>

</div>
</div>
<div class='git-project-right-actions pull-right'>
<div class='ui basic orange button' id='btn-dl-or-clone'>
Clone or Download
<i class='dropdown icon'></i>
</div>
<div class='ui small modal' id='git-project-download-panel'>
<i class='iconfont icon-close close'></i>
<div class='header'>
Clone/Download
</div>
<div class='content'>
<div class='ui secondary pointing menu mb-2 menu-container'>
<a class='item active' data-text='' data-type='http' data-url='https://gitee.com/opengauss/openGauss-server.git'>HTTPS</a>
<a class='item' data-text='' data-type='ssh' data-url='git@gitee.com:opengauss/openGauss-server.git'>SSH</a>
<a class='item' data-text="The repository has forbidden SVN access. if you need it, please visit: &lt;a target='_blank' href=/opengauss/openGauss-server/settings#function&gt;Repository security settings&lt;/a&gt;" data-type='svn' data-url=''>SVN</a>
<a class='item' data-text="The repository has forbidden SVN access. if you need it, please visit: &lt;a target='_blank' href=/opengauss/openGauss-server/settings#function&gt;Repository security settings&lt;/a&gt;" data-type='svn_ssh' data-url=''>SVN+SSH</a>
<a class="button-box ui basic orange button" href="/opengauss/openGauss-server/repository/archive/master.zip"><i class='icon download'></i>
Download ZIP
</a></div>
<div class='ui fluid right labeled small input download-url-panel mb-2'>
<input type="text" name="project_url_clone" id="project_url_clone" value="https://gitee.com/opengauss/openGauss-server.git" onclick="focus();select()" readonly="readonly" />
<div class='ui basic label copy-icon-box'>
<i class='icon iconfont icon-clone mr-0 btn-copy-clone' data-clipboard-target='#project_url_clone' id='btn-copy-project_clone_url1'></i>
</div>
</div>
<div class='tip-box mb-2'>
Prompt
</div>
<div class='mb-1 clone-url-title'>
To download the code, please copy the following command and execute it in the terminal
</div>
<div class='ui fluid right labeled small input download-url-panel mb-2'>
<input type="text" name="project_clone_url" id="project_clone_url" value="https://gitee.com/opengauss/openGauss-server.git" onclick="focus();select()" readonly="readonly" />
<div class='ui basic label copy-icon-box'>
<i class='icon iconfont icon-clone mr-0 btn-copy-clone' data-clipboard-target='#project_clone_url' id='btn-copy-project_clone_url'></i>
</div>
</div>
<div class='ui fluid right labeled warning-text forbid-warning-text'>

</div>
<div class='http-ssh-item mb-2'>
<div>
To ensure that your submitted code identity is correctly recognized by Gitee, please execute the following command.
</div>
<div class='textarea-box mt-2'>
<textarea class='textarea-content-box' id='global-config-clone' readonly>git config --global user.name userName &#10git config --global user.email userEmail</textarea>
<i class='icon iconfont icon-clone mr-2 btn-copy-clone text-dark' data-clipboard-target='#global-config-clone' id='btn-copy-global-config'></i>
</div>
</div>
<div class='ssh-item item-panel-box'>
<div class='mb-2'>
When using the SSH protocol for the first time to clone or push code, follow the prompts below to complete the SSH configuration.
</div>
<div class='mb-1'>
<span>1</span>
Generate RSA keys.
</div>
<div class='ui fluid right labeled small input mb-2'>
<input type="text" name="ssh_keygen_clone" id="ssh_keygen_clone" value="ssh-keygen -t rsa" onclick="focus();select()" readonly="readonly" />
<div class='ui basic label copy-icon-box'>
<i class='icon iconfont icon-clone mr-0 btn-copy-clone' data-clipboard-target='#ssh_keygen_clone' id='btn-copy-ssh_keygen'></i>
</div>
</div>
<div class='mb-1'>
<span>2</span>
Obtain the content of the RSA public key and configure it in <a href='/profile/sshkeys' target="_blank">SSH Public Keys</a>
</div>
<div class='ui fluid right labeled small input mb-2'>
<input type="text" name="id_rsa_clone" id="id_rsa_clone" value="cat ~/.ssh/id_rsa.pub" onclick="focus();select()" readonly="readonly" />
<div class='ui basic label copy-icon-box'>
<i class='icon iconfont icon-clone mr-0 btn-copy-clone' data-clipboard-target='#id_rsa_clone' id='btn-copy-d_rsa'></i>
</div>
</div>
</div>
<div class='svn-item item-panel-box'>
<div class='mb-1 mt-2'>
To use SVN on Gitee, please visit <a href='https://help.gitee.com/enterprise/code-manage/%E4%BB%A3%E7%A0%81%E6%89%98%E7%AE%A1/%E4%BB%A3%E7%A0%81%E4%BB%93%E5%BA%93/Gitee%20SVN%E6%94%AF%E6%8C%81' target="_blank">the usage guide</a>
</div>
</div>
<div class='http-item item-panel-box'>
<div class='mb-2 mt-2'>
When using the HTTPS protocol, the command line will prompt for account and password verification as follows. For security reasons, Gitee recommends <a href='/profile/personal_access_tokens' target="_blank">configure and use personal access tokens</a> instead of login passwords for cloning, pushing, and other operations.
</div>
<div>Username for 'https://gitee.com': userName</div>
<div class='mb-1'>
<span>Password for 'https://userName@gitee.com':</span>
<span>#</span>
<span>
Private Token
</span>
</div>
</div>

</div>
</div>
<style>
  #git-project-download-panel {
    top: 90px !important; }
    #git-project-download-panel input {
      color: #40485b !important; }
    #git-project-download-panel .textarea-box {
      width: 100%;
      height: 60px;
      color: #9d9d9d;
      border-radius: 2px;
      background-color: #F5F5F5 !important;
      display: -webkit-box;
      display: -ms-flexbox;
      display: flex;
      -webkit-box-align: center;
          -ms-flex-align: center;
              align-items: center; }
    #git-project-download-panel .menu-container {
      font-weight: bold;
      border-color: rgba(0, 0, 0, 0.1) !important;
      border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important; }
      #git-project-download-panel .menu-container .item {
        padding: 7px 12px !important; }
    #git-project-download-panel .hr-item {
      color: rgba(39, 41, 43, 0.15) !important; }
    #git-project-download-panel .textarea-content-box {
      width: 100%;
      height: 60px;
      resize: none;
      border: 0px !important;
      background-color: #F5F5F5 !important;
      color: #40485b !important; }
    #git-project-download-panel .btn-copy-clone {
      cursor: pointer;
      color: rgba(0, 0, 0, 0.87) !important; }
    #git-project-download-panel .copy-icon-box {
      background-color: #F5F5F5 !important;
      border-left: 0px !important; }
    #git-project-download-panel .button-box {
      border: 0px !important;
      float: right !important;
      padding-right: 0 !important; }
    #git-project-download-panel .tip-box {
      border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
      padding-bottom: 4px;
      font-weight: 700; }
    #git-project-download-panel .popup-container {
      padding: 8px 12px 4px 12px;
      text-align: center;
      font-size: 14px; }
      #git-project-download-panel .popup-container .ok {
        margin: 12px auto;
        width: 25%;
        min-width: 125px;
        display: block; }
      #git-project-download-panel .popup-container .cancel {
        margin-left: 0; }
</style>
<script>
  $(function () {
    var $btnClone = $('#btn-dl-or-clone')
    var $modalDownload = $('#git-project-download-panel');
    var $input = $('#project_clone_url')
    var $inputUrl = $('#project_url_clone')
    var cloneUrlTitle= $('.clone-url-title')
  
    $('#btn-dl-or-clone').on('click', function (e) {
      e.preventDefault();
      $modalDownload.modal('show');
    })
  
    $modalDownload.find('.menu > .item').on('click', function(e) {
      var $item = $(this).addClass('active');
      $item.siblings().removeClass('active');
      var dataUrl = $item.attr('data-url');
      var cloneUrl = $item.attr('data-url');
      var dataType = $item.attr('data-type')
      var cloneToLocal = 'To download the code, please copy the following command and execute it in the terminal'
      if(dataType=='http'){
        $modalDownload.find('.http-item').show();
        $('.content > .item-panel-box:not(.http-item)').hide();
        $modalDownload.find('.http-ssh-item').show();
        cloneUrl = 'git clone '+dataUrl
      }else if(dataType=='ssh'){
        $modalDownload.find('.ssh-item').show();
        $('.content > .item-panel-box:not(.ssh-item)').hide();
        $modalDownload.find('.http-ssh-item').show();
        cloneUrl = 'git clone '+dataUrl
      }else if(dataType=='svn') {
        $('.content > .item-panel-box:not(.svn-item)').hide();
        $modalDownload.find('.svn-item').show();
        $modalDownload.find('.http-ssh-item').hide();
        cloneUrl = 'svn checkout '+dataUrl
      }else {
        $('.content > .item-panel-box:not(.svn-item)').hide();
        $modalDownload.find('.svn-item').show();
        $modalDownload.find('.http-ssh-item').hide();
        cloneUrl = 'svn checkout '+dataUrl
      }
      if (dataUrl) {
        $modalDownload.find('.download-url-panel').show();
        $input.val(cloneUrl);
        $inputUrl.val(dataUrl)
        cloneUrlTitle.show();
        $modalDownload.find('.forbid-warning-text').html('');
      } else {
        $modalDownload.find('.download-url-panel').hide();
        //$modalDownload.find('.svn-item').hide();
        cloneUrlTitle.hide();
        $modalDownload.find('.forbid-warning-text').html($item.attr('data-text') || '');
      }
      $.cookie('remote_way', $item.attr('data-type'), { expires: 365, path: '/' });
    }).filter('[data-type="' + ($.cookie('remote_way') || 'http') + '"]').trigger('click');
  
    $('.btn-copy-clone').popup({
      content: 'Copy to clipboard',
    }).on('click', function(e) {
      e.stopPropagation();
      return false;
    }).each(function(_, btnCopy) {
      var $btnCopy = $(btnCopy);
      new Clipboard(btnCopy).on('success', function() {
        $btnCopy.popup('destroy').popup({
          content: 'Copied',
          on: 'manual'
        }).popup('show');
        setTimeout(function() {
          $btnCopy.popup('destroy').popup({
            content: 'Copy to clipboard'
          });
        }, 2000);
      });
    });
    var $downloadBtn= $('.unlogin-download-btn')
    var $popupContainer = $('.popup-container')
    $downloadBtn.popup({
      popup : $('.custom.popup'),
      position   : 'bottom right',
    }).on('click', function(e) {
      $downloadBtn.popup('destroy').popup({
        popup : $('.custom.popup'),
        on: 'manual',
        position   : 'bottom right',
      }).popup('show');
      setTimeout(function() {
        $downloadBtn.popup('hide');
      }, 2000);
  
    })
  })
</script>

</div>
<div class='d-inline pull-right' id='git-project-root-actions'>
<div class='ui horizontal list repo-action-list d-flex d-align-center repo-action-list-right'>
<div class='item search-box-container'>
<div class='ui icon input search-input' id='search-box'>
<input class='search-file-name' maxlength='40' placeholder='Search' type='text'>
</div>
<a class='d-flex d-align-center head-search-file-btn' id='search-file-btn'>
<span class='iconify' data-icon='gitee:search' style='font-size: 16px;color:#979CAC;margin-right:10px'></span>
</a>
<div class='filter-file-container' style='display: none;'></div>
</div>
<script>
  (function() {
    const $dropdown = $('#git-tree-file[data-id="git-tree-file"]');
    const dropdownEl = $dropdown[0];
    const $plusBox = $dropdown.closest('.plus-box');
    const dropdownAppendToBody = false;
    let allowHide = true;
  
    if (dropdownAppendToBody) {
      document.body.addEventListener('click', function(e) {
        allowHide = true;
        let current = e.target;
        while (current !== null) {
          if (current === dropdownEl) {
            allowHide = false;
            break;
          }
          current = current.parentElement;
        }
        if (allowHide) $dropdown.dropdown('hide');
      }, true);
    }
  
    $dropdown.dropdown({
      action: 'hide',
      onHide: function () {
        $plusBox.removeClass('click-active');
  
        return allowHide;
      },
      onShow: function () {
        $plusBox.addClass('click-active');
  
        if (!dropdownAppendToBody) return;
        const $wrapper = this.$menuWrapper || $('<div class="ui top dropdown active visible"></div>');
        const offset = $(this).offset();
        $wrapper.css({
          position: 'absolute',
          top: offset.top,
          left: offset.left,
          marginTop: '1rem',
          zIndex: 1000
        });
  
        if (this.loaded) return;
  
        // destroy prev dropdown
        document.querySelectorAll('.ui.dropdown[data-prev-dropdown]').forEach(function(el) {
          el.parentNode.removeChild(el);
        });
        const $menu = $(this).find('.menu');
        $menu.css({
          display: 'block',
          border: '1px solid rgba(34,36,38,0.15)',
          borderRadius: '4px',
          boxShadow: '0px 2px 3px 0px rgba(34, 36, 38, 0.15)'
        });
        // 移动到 body
        $wrapper.append($menu);
        $wrapper.appendTo('body');
        $wrapper.attr('data-prev-dropdown', '');
        this.$menuWrapper = $wrapper;
        this.loaded = true;
      }
    });
  })();
  
  $('#git-project-root-actions #git-tree-file').on('click', function() {
    $('#git-project-root-actions .plus-box').addClass('click-active')
    $('#git-project-root-actions .repo-dropdown-box').addClass('transition visible')
  })
  
  $('.disabled-upload-readonly').popup({
    content: "Readonly directory does not allow uploading files",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-create-folder').popup({
    content: "Readonly directory does not allow directory creation",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-create-file').popup({
    content: "Readonly directory does not allow files creation",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-create-submodule').popup({
    content: "Readonly directory does not allow submodule creation",
    className: {
      popup: 'ui popup',
    },
    position: 'bottom center',
  })
  $('.disabled-upload-readonly, .disabled-create-folder, .disabled-create-file, .disabled-create-submodule').click(function() {
    return false
  })
</script>
<style>
  .disabled-upload-readonly, .disabled-create-file, .disabled-create-folder, .disabled-create-submodule {
    background-color: #dcddde !important;
    color: rgba(0, 0, 0, 0.4) !important;
    opacity: 0.3 !important;
    background-image: none !important;
    -webkit-box-shadow: none !important;
            box-shadow: none !important; }
</style>

<div class='item compare-box' data-content='Compare view'>
<a class="ui d-flex d-align-center webide" target="_blank" href="/opengauss/openGauss-server/compare/master...master"><span class='iconify' data-icon='gitee:diff' style='font-size: 16px;color:#979CAC;margin-right:12px'></span>
</a></div>
</div>
<script>
  $('.webIDE-box').popup()
  $('.compare-box').popup()
</script>
<script src="https://cn-assets.gitee.com/assets/file_search/app-21e8df8af6aa09b8995390509269205b.js"></script>
<style>
  .filter-file-container-hide {
    display: none !important; }
</style>

</div>
<div class='breadcrumb_path path-breadcrumb-contrainer' id='git-project-breadcrumb'>
<div class='ui breadcrumb path project-path-breadcrumb d-flex' id='path-breadcrumb'>
<div class='mr-1 hide' id='file-iconify-wrapper'>
<div class='file-iconify-item d-align-center mr-1' onclick="$('.project-left-side-contaner').show();$('#file-iconify-wrapper').addClass('hide').removeClass('d-align-center');">
<span class='iconify' data-icon='gitee:sidebar-collapse' style='font-size: 16px;'></span>
</div>
<div class='left-project-branch-item project-branch-item' style='display: inline-block;'>
<input type="hidden" name="path" id="path" value="README.en.md" />
<div class='ui top left pointing dropdown gradient button dropdown-has-tabs' id='git-project-branch'>
<input type="hidden" name="ref" id="ref" value="master" />
<div class='default text'>
master
</div>
<i class='dropdown icon'></i>
<div class='menu'>
<div class='ui left icon input'>
<span class='dropdown-search-icon iconify' data-icon='gitee:search' style='font-size: 14px;'></span>
<input class='search-branch' placeholder='Search branch' type='text'>
</div>
<div class='tab-menu project-branch-tab-menu d-flex'>
<div class='tab-menu-item' data-placeholder='Search branches' data-tab='branches'>
Branches (20)
</div>
<div class='tab-menu-item' data-placeholder='Search tags' data-tab='tags'>
Tags (32)
</div>
<div class='d-align-center' style='flex:1;justify-content:end;'>
<div class='tab-menu-action' data-tab='branches'>
<a class="ui link button" href="/opengauss/openGauss-server/branches">Manage</a>
</div>
<div class='tab-menu-action' data-tab='tags'>
<a class="ui link button" href="/opengauss/openGauss-server/tags">Manage</a>
</div>
</div>
</div>
<div class='tab scrolling menu' data-tab='branches' id='branches_panel'>
<div data-value="master" class="item" title="master"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>master</span></div>
<div data-value="6.0.0" class="item" title="6.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>6.0.0</span></div>
<div data-value="3.0.0" class="item" title="3.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>3.0.0</span></div>
<div data-value="5.0.0" class="item" title="5.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>5.0.0</span></div>
<div data-value="feature_1230_4" class="item" title="feature_1230_4"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>feature_1230_4</span></div>
<div data-value="datavec_poc" class="item" title="datavec_poc"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>datavec_poc</span></div>
<div data-value="tp_poc" class="item" title="tp_poc"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>tp_poc</span></div>
<div data-value="7.0.0-RC2" class="item" title="7.0.0-RC2"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>7.0.0-RC2</span></div>
<div data-value="7.0.0-RC1" class="item" title="7.0.0-RC1"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>7.0.0-RC1</span></div>
<div data-value="master_bak08271930" class="item" title="master_bak08271930"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>master_bak08271930</span></div>
<div data-value="iud_dev" class="item" title="iud_dev"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>iud_dev</span></div>
<div data-value="dev_board" class="item" title="dev_board"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>dev_board</span></div>
<div data-value="5.1.0" class="item" title="5.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>5.1.0</span></div>
<div data-value="kms" class="item" title="kms"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>kms</span></div>
<div data-value="2.0.0" class="item" title="2.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>2.0.0</span></div>
<div data-value="3.1.0" class="item" title="3.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>3.1.0</span></div>
<div data-value="2.1.0" class="item" title="2.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>2.1.0</span></div>
<div data-value="1.1.0" class="item" title="1.1.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.1.0</span></div>
<div data-value="1.0.1" class="item" title="1.0.1"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.0.1</span></div>
<div data-value="1.0.0" class="item" title="1.0.0"><span class="iconify" data-icon="gitee:branch" style="font-size: 13px;margin-right:4px; color:#8C92A4"></span> <span>1.0.0</span></div>
</div>
<div class='tab scrolling menu' data-tab='tags' id='tags_panel'>
<div class='item' data-value='v6.0.3'>v6.0.3</div>
<div class='item' data-value='v5.0.5'>v5.0.5</div>
<div class='item' data-value='v7.0.0-RC2'>v7.0.0-RC2</div>
<div class='item' data-value='v6.0.2'>v6.0.2</div>
<div class='item' data-value='v7.0.0-RC1'>v7.0.0-RC1</div>
<div class='item' data-value='v6.0.1'>v6.0.1</div>
<div class='item' data-value='v3.0.6'>v3.0.6</div>
<div class='item' data-value='v6.0.0'>v6.0.0</div>
<div class='item' data-value='v3.0.5B009'>v3.0.5B009</div>
<div class='item' data-value='v5.0.3'>v5.0.3</div>
<div class='item' data-value='v5.0.2'>v5.0.2</div>
<div class='item' data-value='v6.0.0-RC1'>v6.0.0-RC1</div>
<div class='item' data-value='v3.0.5'>v3.0.5</div>
<div class='item' data-value='v5.0.1'>v5.0.1</div>
<div class='item' data-value='v5.1.0'>v5.1.0</div>
<div class='item' data-value='5.1.0'>5.1.0</div>
<div class='item' data-value='v5.0.0'>v5.0.0</div>
<div class='item' data-value='v3.0.3'>v3.0.3</div>
<div class='item' data-value='v3.1.1'>v3.1.1</div>
<div class='item' data-value='v3.0.2'>v3.0.2</div>
</div>
</div>
</div>
<style>
  .iconfont.icon-shieldlock {
    color: #8c92a4;
  }
  .dropdown-search-icon {
    position: absolute;
    top: 8px;
    left: 11px;
  }
</style>
<style>
  #git-project-branch .project-branch-tab-menu, .project-branch-item .project-branch-tab-menu {
    padding-left: 0px !important;
    padding-right: 0px !important;
    margin: 0 11px !important;
    border-bottom: 1px solid #dfe3e9 !important; }
  #git-project-branch .ui.dropdown .menu, .project-branch-item .ui.dropdown .menu {
    width: 360px !important; }
    #git-project-branch .ui.dropdown .menu .item, .project-branch-item .ui.dropdown .menu .item {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap; }
  #git-project-branch .tab-menu-actions, .project-branch-item .tab-menu-actions {
    position: absolute;
    right: 0px !important;
    bottom: 0.357em; }
  #git-project-branch .tab-menu-action, .project-branch-item .tab-menu-action {
    position: relative !important;
    right: 0px !important;
    bottom: 0px !important; }
  #git-project-branch .menu::after, .project-branch-item .menu::after {
    display: none !important; }
</style>
<script>
  var $branchesDropdown = $('#branches_panel');
  var $tagsDropdown = $('#tags_panel');
  var $searchNameInput = $('.search-branch');
  var concurrentRequestLock = false;
  var filterXSS = window.filterXSS;
  var search_text = "";
  var branch_page_number = 1;
  var branch_total_pager = Math.ceil(20 / 20) || 1
  
  var flag_is_loading = false;
  var flag_page_number = 1;
  var flag_total_pager = Math.ceil(32 / 20) || 1
  
  $branchesDropdown.scroll(function() {
    var branchesPanel = document.getElementById('branches_panel');
    var numOfBranches = $branchesDropdown.children().length;
    if (branchesPanel.clientHeight + branchesPanel.scrollTop + 37 > branchesPanel.scrollHeight && numOfBranches < 20) {
      debounceLoadMoreBranches.call();
    }
  });
  function resetFlagVal() {
    flag_is_loading = false;
    flag_page_number = 1;
    flag_total_pager = 1;
  
    concurrentRequestLock = false
    search_text = "";
    branch_page_number = 1;
    branch_total_pager = 1
  }
  $searchNameInput.on('input', window.globalUtils.debouce(function (e) {
    resetFlagVal()
    var $currentTab = $('.tab-menu-action.active');
    var numOfBranches = $branchesDropdown.children().length;
    var searchWord = $searchNameInput.val().trim();
    search_text = searchWord
    if($currentTab.data('tab') === 'branches') {
      if (searchWord !== "") {
        loadData(searchWord,1);
      } else {
        loadData();
      }
    }
    var numOfTags = $tagsDropdown.children().length;
    if($currentTab.data('tab') === 'tags') {
      if (searchWord !== "") {
        fetchTags(searchWord,1);
      } else {
        fetchTags();
      }
    }
  }, 500));
  
  function toggleNoResultView($popPanel) {
    let no_data_html= `<div class='mt-1 mb-1 d-flex-center'> <span>暂无数据</span> </div>`
    $popPanel.append(no_data_html)
  }
  var debounceLoadMoreBranches = window.globalUtils.debouce(function () {
    if (concurrentRequestLock) return;
    branch_page_number += 1;
    if (branch_page_number > branch_total_pager) return;
    loadData(search_text, branch_page_number);
  }, 350);
  
  function loadData(search, page) {
    if (concurrentRequestLock) { return; }
    concurrentRequestLock = true;
  
    var searchParams = search || "";
    var pageParams = page || 1;
    $.ajax({
      url: "/" + gon.user_project + "/branches/names.json",
      type: 'GET',
      data: {
        search: searchParams,
        page: pageParams,
      },
      dataType: 'json',
      success: function (data) {
        branch_total_pager = data.total_pages;
        var html = '';
  
        if (pageParams === 1) {
          $branchesDropdown.empty();
        }
        data.branches.forEach(function (branch) {
          var protectRule = '';
          var branchName = filterXSS(branch.name);
          var icon = 'gitee:branch'
          if(branch.branch_type.value === 1) {
            var rule = filterXSS(branch.protection_rule.wildcard);
            protectRule = `<i
                class="iconfont icon-shieldlock protected-branch-popup"
                data-title="受保护分支"
                data-content='保护规则： ${rule}'
              >
              </i>`
            icon ='gitee:pen-lock'
          }else if(branch.branch_type.value === 2) {
            icon ='gitee:pen-ban'
          }
          var branchIcon = `<span class="iconify" data-icon=${icon} style="font-size: 13px; margin-right:4px; color:#8C92A4"></span>`
          html += `<div data-value='${branchName}' class="item">
                    ${branchIcon} 
                    <span>${branchName}</span> ${protectRule}
                    </div>`
        });
        $branchesDropdown.append(html);
        $('.protected-branch-popup').popup()
        if (pageParams === 1 && data.count === 0) {
          toggleNoResultView($branchesDropdown);
        }
      },
      complete: function () {
        concurrentRequestLock = false;
      }
    });
  }
  
  
  
  $tagsDropdown.scroll(function() {
    var tagsPanel = document.getElementById('tags_panel');
    var numOfTags = $tagsDropdown.children().length;
    if (tagsPanel.clientHeight + tagsPanel.scrollTop + 37 > tagsPanel.scrollHeight && numOfTags < 32) {
      debounceLoadMore.call();
    }
  });
  var debounceLoadMore = window.globalUtils.debouce(function () {
    if (flag_is_loading) return;
    flag_page_number += 1;
    if (flag_page_number > flag_total_pager) return;
    fetchTags(search_text, flag_page_number);
  }, 350);
  
  function fetchTags(search, page) {
    var searchParams = search || "";
    var pageParams = page || 1;
  
    if (flag_is_loading) return;
    flag_is_loading = true;
  
    $.ajax({
      url: "/" + gon.user_project + "/tags/names.json",
      data: {
        search: searchParams,
        page: pageParams,
      },
      type: "GET",
      xhrFields: {
        withCredentials: true,
      },
      success: function (data) {
        flag_total_pager = data.total_pages;
        if (pageParams === 1) {
          $tagsDropdown.html('');
        }
        data.tags.forEach((tag) => {
          const itemDiv = document.createElement('div');
          itemDiv.classList.add('item');
          itemDiv.setAttribute('data-value', tag.name);
          itemDiv.innerText = window.filterXSS(tag.name);
          $tagsDropdown.append(itemDiv)
        });
        if (pageParams === 1 && data.count === 0) {
          toggleNoResultView($tagsDropdown);
        }
      },
      error: function () {
      },
      complete: function () {
        flag_is_loading = false;
      },
    });
  }
  $('.project-branch-tab-menu').on('click','.tab-menu-item', function (e) {
    var $currentTab = $(this).data('tab')
    if($currentTab === 'branches') {
      $searchNameInput.val('')
      search_text = '';
      loadData()
    }
    if($currentTab === 'tags') {
      $searchNameInput.val('')
      search_text = '';
      fetchTags();
    }
  })
</script>

<script>
  $(function () {
    var curNode = $('.git-project-branch-item')
    if (true ){
      curNode = $('.left-project-branch-item')
    }else {
      curNode = $('.git-project-branch-item')
    }
    Gitee.initTabsInDropdown(curNode.find('#git-project-branch').dropdown({
      fullTextSearch: true,
      selectOnKeydown: false,
      direction: 'downward',
      action: function (text,value,el) {
        var oItemOrInitObject = el[0] || el
        var isNotSelect = oItemOrInitObject.dataset.tab && oItemOrInitObject.dataset.tab === 'branches'
        if(isNotSelect){
          console.warn("You didn't choose a branch")
          return
        }
        var path = $('#path').val();
        var href = ['/opengauss/openGauss-server/tree', encodeURIComponent(value), path].join('/');
        window.location.href = href;
        return true
      },
      onNoResults: function (searchTerm) {
        //未找到结果
        return true
      },
    }));
    $('.protected-branch-popup').popup()
  })
</script>

</div>
</div>
<div class='tree-breadcrumb-wrapper'>
<a data-direction="back" class="section repo-name" style="font-weight: bold" href="/opengauss/openGauss-server/tree/master">openGauss-server
</a><div class='divider'>
/
</div>
<strong>
README.en.md
</strong>
<i class='iconfont icon-clone ml-1' data-clipboard-text='README.en.md' id='btn-copy-file-path'></i>
</div>
</div>
<style>
  #btn-copy-file-path {
    vertical-align: middle;
    cursor: pointer;
  }
  .file-iconify-item {
      display: inline-block !important;
      cursor: pointer;
      border-radius: 4px;
      margin-right: 8px;
      cursor: pointer;
      width: 32px;
      height: 32px;
      text-align: center;
      &:hover {
        background-color: #F5F7FA
      }
    }
  .dropdown.project-branch-item {
    #git-project-branch {
      min-width: 92px !important;
    }
    .icon.dropdown {
      float: right !important;
      margin-top: 2px !important
    }
    .ui.dropdown .menu.transition.visible {
      min-width: 288px !important;
      max-width: 360px !important
      .item {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
</style>
<script>
  $btnCopy = $('#btn-copy-file-path')
  $btnCopy.popup({
    content: 'Copy path'
  })
  
  if ($btnCopy[0]) {
    new Clipboard($btnCopy[0]).on('success', function() {
      $btnCopy.popup('destroy').popup({
        content: 'Copied',
        on: 'manual'
      }).popup('show');
      setTimeout(function () {
        $btnCopy.popup('destroy').popup({
          content: 'Copy path'
        });
      }, 2000)
    });
  }
</script>


</div>
<div class='ui horizontal list repo-action-list branches-tags' style='display: none;'>
<div class='item'>
<a class="ui blank button" href="/opengauss/openGauss-server/branches"><i class='iconfont icon-branches'></i>
Branches 20
</a></div>
<div class='item mr-3'>
<a class="ui blank button" href="/opengauss/openGauss-server/tags"><i class='iconfont icon-tag'></i>
Tags 32
</a></div>
</div>
</div>
<script src="https://cn-assets.gitee.com/webpacks/parse_blob_form_scheme-f74db29bb977414ba0cb.bundle.js"></script>
<script>
  if(window.gon.locale == 'en')
    $('.branches-tags').css('margin-top', '12px')
   // 仓库页面切换路径时: 刷新 yaml 错误检查
  $(window).on('pjax-complete:file-show', function () {
    window.parseBlobFormScheme && window.parseBlobFormScheme($('.js-blob-data').data('blob'));
  });
</script>

<style>
  .ui.dropdown .menu > .header {
    text-transform: none; }
</style>
<script>
  $(function () {
    var $tip = $('#apk-download-tip');
    if (!$tip.length) {
      return;
    }
    $tip.find('.btn-close').on('click', function () {
      $tip.hide();
    });
  });
  (function(){
    function pathAutoRender() {
      var $parent = $('#git-project-bread'),
          $child = $('#git-project-bread').children('.ui.horizontal.list'),
          mainWidth = 0;
      $child.each(function (i,item) {
        mainWidth += $(item).width()
      });
      $('.breadcrumb.path.fork-path').remove();
      if (mainWidth > 995) {
        $('#path-breadcrumb').hide();
        $parent.append('<div class="ui breadcrumb path fork-path">' + $('#path-breadcrumb').html() + '<div/>')
      } else {
        $('#path-breadcrumb').show();
      }
    }
    window.pathAutoRender = pathAutoRender;
    pathAutoRender();
  })();
</script>

<div class='row column tree-holder' id='tree-holder'>
<div class='tree-content-holder' id='tree-content-holder'>
<div class='file_holder'>
<div class='file_title'>
<div class='mb-2 file_breadcrumb_wrapper' style='display: none;'>
<div class='tree-breadcrumb-wrapper d-flex pl-1 pb-1'>
<a data-direction="back" class="section repo-name" style="font-weight: bold" href="/opengauss/openGauss-server/tree/master">openGauss-server
</a><div class='divider'>
/
</div>
<strong>
README.en.md
</strong>
</div>
<div class='file_title_divider'></div>
</div>
<div class='blob-header-title'>
<div class='blob-description'>
<i class="iconfont icon-file"></i>
<span class='file_name' title='README.en.md'>
README.en.md
</span>
<small>27.12 KB</small>
</div>
<div class='options'><div class='ui mini buttons basic'>
<textarea name="blob_raw" id="blob_raw" style="display:none;">
![openGauss Logo](doc/openGauss-logo.png &quot;openGauss logo&quot;)&#x000A;============================================================&#x000A;&#x000A;- [What Is openGauss?](#What Is openGauss?)&#x000A;- [Installation](#Installation)&#x000A;    - [Creating a Configuration File](#Creating a Configuration File)&#x000A;    - [Initializing the Installation Environment](#Initializing the Installation Environment)&#x000A;- [Executing Installation](#Executing Installation)&#x000A;  [Uninstalling the openGauss](#Uninstalling the openGauss)&#x000A;- [Compilation](#Compilation)&#x000A;    - [Overview](#Overview)&#x000A;    - [OS and Software Dependency Requirements](# OS and Software Dependency Requirements)&#x000A;    - [Downloading openGauss](# Downloading openGauss)&#x000A;    - [Compiling Third-Party Software](#Compiling Third-Party Software)&#x000A;    - [Compiling by build.sh](#Compiling by build.sh)&#x000A;    - [Compiling by Command](#Compiling by Command)&#x000A;    - [Compiling the Installation Package](#Compiling the Installation Package)&#x000A;- [Quick Start](#Quick Start)&#x000A;- [Docs](#Docs)&#x000A;- [Community](#Community)&#x000A;    - [Governance](#Governance)&#x000A;    - [Communication](#Communication)&#x000A;- [Contribution](#Contribution)&#x000A;- [Release Notes](#Release Notes)&#x000A;- [License](#License)&#x000A;&#x000A;## What Is openGauss?&#x000A;&#x000A;openGauss is an open source relational database management system. It has multi-core high-performance, full link security, intelligent operation and maintenance for enterprise features. openGauss integrates Huawei&#39;s core experience in database field for many years. It optimizes the architecture, transaction, storage engine, optimizer and ARM architecture. At the meantime, openGauss as a global database open source community, aims to further advance the development and enrichment of the database software/hardware application ecosystem.&#x000A;&#x000A;&lt;img src=&quot;doc/openGauss-architecture.png&quot; alt=&quot;opengauss Architecture&quot; width=&quot;600&quot;/&gt;&#x000A;&#x000A;**High Performance**&#x000A;&#x000A;openGauss breaks through the bottleneck of multi-core CPU, 2-way Kunpeng 128 core 1.5 million TPMC.&#x000A;&#x000A;**Partitions**&#x000A;&#x000A;Divide key data structure shared by internal threads into different partitions to reduce lock access conflicts. For example, CLOG uses partition optimization to solve the bottleneck of ClogControlLock.&#x000A;&#x000A;**NUMA Structure**&#x000A;&#x000A;Malloc key data structures help reduce cross CPU access. The global PGPROC array is divided into several parts according to the number of NUMA nodes, solving the bottleneck of ProcArrayLock. &#x000A;&#x000A;**Binding Cores**&#x000A;&#x000A;Bind NIC interrupts to different cores and bind cores to different background threads to avoid performance instability due to thread migration between cores.&#x000A;&#x000A;**ARM Optimization**&#x000A;&#x000A;Optimize atomic operations based on ARM platform LSE instructions, impletmenting efficient operation of critical sections.&#x000A;&#x000A;**SQL Bypass**&#x000A;&#x000A;Optimize SQL execution process through SQL bypass, reducing CPU execution overhead.&#x000A;&#x000A;**High Reliability**&#x000A;&#x000A;Under normal service loads, the RTO is less than 10 seconds, reducing the service interruption time caused by node failure.&#x000A;&#x000A;**Parallel Recovery**&#x000A;&#x000A;When the Xlog is transferred to the standby node, the standby node flushs the Xlog to storage medium. At the mean time, the Xlog is sent to the redo recovery dispatch thread. The dispatch thread sends the Xlog to multiple parallel recovery threads to replay. Ensure that the redo speed of the standby node keeps up with the generation speed of the primary host. The standby node is ready in real time, which can be promoted to primary instantly. &#x000A;&#x000A;**MOT Engine (beta release)**&#x000A;&#x000A;The Memory-Optimized Tables (MOT) storage engine is a transactional rowstore optimized for many-core and large memory and delivering extreme OLTP performance and high resources utilization. With data and indexes stored totally in-memory, a NUMA-aware design, algorithms that eliminate lock and latch contention and query native compilation (JIT), MOT provides low latency data access and more efficient transaction execution. See [MOT Engine documentation](https://opengauss.org/en/docs/2.1.0/docs/Developerguide/mot.html).&#x000A;&#x000A;**Security**&#x000A;&#x000A;openGauss supports account management, account authentication, account locking, password complexity check, privilege management and verification, transmission encryption, and operation audit, protecting service data security.&#x000A;&#x000A;**Easy Operation and Maintenance**&#x000A;&#x000A;openGauss integrates AI algorithms into databases, reducing the burden of database maintenance.&#x000A;&#x000A;- **SQL Prediction**&#x000A;&#x000A;openGauss supports SQL execution time prediction based on collected historical performance data.&#x000A;&#x000A;- **SQL Diagnoser **&#x000A;&#x000A;openGauss supports the diagnoser for SQL execution statements, finding out slow queries in advance..&#x000A;&#x000A;- **Automatical Parameter Adjustment**&#x000A;&#x000A;openGauss supports automatically adjusting database parameters, reducing the cost and time of parameter adjustment.&#x000A;&#x000A;## Installation&#x000A;&#x000A;### Creating a Configuration File&#x000A;&#x000A;Before installing the openGauss, you need to create a configuration file. The configuration file in the XML format contains the information about the server where the openGauss is deployed, installation path, IP address, and port number. This file is used to guide how to deploy the openGauss. You need to configure the configuration file according to the actual deployment requirements.&#x000A;&#x000A;The following describes how to create an XML configuration file based on the deployment solution of one primary node and one standby node.&#x000A;The information in bold is only an example. You can replace it as required. Each line of information is commented out.&#x000A;&#x000A;```&#x000A;&lt;?xml version=&quot;1.0&quot; encoding=&quot;utf-8&quot;?&gt;&#x000A;&lt;ROOT&gt;&#x000A;&lt;!-- Overall information --&gt;&#x000A;  &lt;CLUSTER&gt;&#x000A;  &lt;!-- Database name --&gt;&#x000A;    &lt;PARAM name=&quot;clusterName&quot; value=&quot;Cluster_template&quot; /&gt;&#x000A;	&lt;!-- Database node name (hostname) --&gt;&#x000A;    &lt;PARAM name=&quot;nodeNames&quot; value=&quot;node1_hostname,node2_hostname&quot;/&gt;&#x000A;	&lt;!-- Database installation path --&gt;&#x000A;    &lt;PARAM name=&quot;gaussdbAppPath&quot; value=&quot;/opt/huawei/install/app&quot; /&gt;&#x000A;	&lt;!-- Log directory --&gt;&#x000A;    &lt;PARAM name=&quot;gaussdbLogPath&quot; value=&quot;/var/log/omm&quot; /&gt;&#x000A;	&lt;!-- Temporary file directory --&gt;&#x000A;    &lt;PARAM name=&quot;tmpMppdbPath&quot; value=&quot;/opt/huawei/tmp&quot;/&gt;&#x000A;	&lt;!-- Database tool directory --&gt;&#x000A;    &lt;PARAM name=&quot;gaussdbToolPath&quot; value=&quot;/opt/huawei/install/om&quot; /&gt;&#x000A;	&lt;!--Directory of the core file of the database --&gt;&#x000A;    &lt;PARAM name=&quot;corePath&quot; value=&quot;/opt/huawei/corefile&quot;/&gt;&#x000A;	&lt;!-- Node IP addresses corresponding to the node names, respectively --&gt;&#x000A;    &lt;PARAM name=&quot;backIp1s&quot; value=&quot;192.168.0.1,192.168.0.2&quot;/&gt;&#x000A;  &lt;/CLUSTER&gt;&#x000A;&lt;!-- Information about node deployment on each server --&gt;&#x000A;  &lt;DEVICELIST&gt;&#x000A;  &lt;!-- Information about the node deployment on node1 --&gt;&#x000A;    &lt;DEVICE sn=&quot;node1_hostname&quot;&gt;&#x000A;	  &lt;!-- Host name of node1 --&gt;&#x000A;      &lt;PARAM name=&quot;name&quot; value=&quot;node1_hostname&quot;/&gt;&#x000A;	  &lt;!-- AZ where node1 is located and AZ priority --&gt;&#x000A;      &lt;PARAM name=&quot;azName&quot; value=&quot;AZ1&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;azPriority&quot; value=&quot;1&quot;/&gt;&#x000A;	  &lt;!-- IP address of node1. If only one NIC is available for the server, set backIP1 and sshIP1 to the same IP address. --&gt;&#x000A;      &lt;PARAM name=&quot;backIp1&quot; value=&quot;192.168.0.1&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;sshIp1&quot; value=&quot;192.168.0.1&quot;/&gt;&#x000A;      &lt;!--DBnode--&gt;&#x000A;      &lt;PARAM name=&quot;dataNum&quot; value=&quot;1&quot;/&gt;&#x000A;	  &lt;!-- Database node port number --&gt;&#x000A;      &lt;PARAM name=&quot;dataPortBase&quot; value=&quot;15400&quot;/&gt;&#x000A;	  &lt;!-- Data directory on the primary database node and data directories of standby nodes --&gt;&#x000A;      &lt;PARAM name=&quot;dataNode1&quot; value=&quot;/opt/huawei/install/data/dn,node2_hostname,/opt/huawei/install/data/dn&quot;/&gt;&#x000A;	  &lt;!-- Number of nodes for which the synchronization mode is set on the database node --&gt;&#x000A;      &lt;PARAM name=&quot;dataNode1_syncNum&quot; value=&quot;0&quot;/&gt;&#x000A;    &lt;/DEVICE&gt;&#x000A;  &lt;!-- Information about the node deployment on node2 --&gt;&#x000A;    &lt;DEVICE sn=&quot;node2_hostname&quot;&gt;&#x000A;	  &lt;!-- Host name of node2 --&gt;&#x000A;      &lt;PARAM name=&quot;name&quot; value=&quot;node2_hostname&quot;/&gt;&#x000A;	  &lt;!-- AZ where node1 is located and AZ priority --&gt;&#x000A;      &lt;PARAM name=&quot;azName&quot; value=&quot;AZ1&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;azPriority&quot; value=&quot;1&quot;/&gt;&#x000A;	  &lt;!-- IP address of node1. If only one NIC is available for the server, set backIP1 and sshIP1 to the same IP address. --&gt;&#x000A;      &lt;PARAM name=&quot;backIp1&quot; value=&quot;192.168.0.2&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;sshIp1&quot; value=&quot;192.168.0.2&quot;/&gt;&#x000A;    &lt;/DEVICE&gt;&#x000A;  &lt;/DEVICELIST&gt;&#x000A;&lt;/ROOT&gt;&#x000A;```&#x000A;&#x000A;### Initializing the Installation Environment&#x000A;&#x000A;After the openGauss configuration file is created, you need to run the gs_preinstall script to prepare the account and environment so that you can perform openGauss installation and management operations with the minimum permission, ensuring system security.&#x000A;&#x000A;**Precautions**&#x000A;&#x000A;- You must check the upper-layer directory permissions to ensure that the user has the read, write, and execution permissions on the installation package and configuration file directory.&#x000A;- The mapping between each host name and IP address in the XML configuration file must be correct.&#x000A;- Only user root is authorized to run the gs_preinstall command.&#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. Log in to any host where the openGauss is to be installed as user root and create a directory for storing the installation package as planned.&#x000A;&#x000A;   ```&#x000A;   mkdir -p /opt/software/openGauss&#x000A;   chmod 755 -R /opt/software&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTE:** &#x000A;   &gt;&#x000A;   &gt; - Do not create the directory in the home directory or subdirectory of any openGauss user because you may lack permissions for such directories.&#x000A;   &gt; - The openGauss user must have the read and write permissions on the /opt/software/openGauss directory.&#x000A;&#x000A;2. The release package is used as an example. Upload the installation package openGauss_x.x.x_PACKAGES_RELEASE.tar.gz and the configuration file clusterconfig.xml to the directory created in the previous step.&#x000A;&#x000A;3. Go to the directory for storing the uploaded software package and decompress the package.&#x000A;&#x000A;   ```&#x000A;   cd /opt/software/openGauss&#x000A;   tar -zxvf openGauss_x.x.x_PACKAGES_RELEASE.tar.gz&#x000A;   ```&#x000A;&#x000A;4. Decompress the openGauss-x.x.x-openEULER-64bit.tar.gz package.&#x000A;&#x000A;   ```&#x000A;   tar -zxvf openGauss-x.x.x-openEULER-64bit.tar.gz&#x000A;   ```&#x000A;&#x000A;   After the installation package is decompressed, the script subdirectory is automatically generated in /opt/software/openGauss. OM tool scripts such as gs_preinstall are generated in the script subdirectory.&#x000A;&#x000A;5. Go to the directory for storing tool scripts.&#x000A;&#x000A;   ```&#x000A;   cd /opt/software/openGauss/script&#x000A;   ```&#x000A;&#x000A;6. To ensure that the OpenSSL version is correct, load the lib library in the installation package before preinstallation. Run the following command. {packagePath} indicates the path where the installation package is stored. In this example, the path is /opt/software/openGauss.&#x000A;&#x000A;   ```&#x000A;   export LD_LIBRARY_PATH={packagePath}/script/gspylib/clib:$LD_LIBRARY_PATH&#x000A;   ```&#x000A;&#x000A;&#x000A;7. To ensure successful installation, check whether the values of hostname and /etc/hostname are the same. During preinstallation, the host name is checked.&#x000A;&#x000A;8. Execute gs_preinstall to configure the installation environment. If the shared environment is used, add the --sep-env-file=ENVFILE parameter to separate environment variables to avoid mutual impact with other users. The environment variable separation file path is specified by users.&#x000A;   Execute gs_preinstall in interactive mode. During the execution, the mutual trust between users root and between clusteropenGauss users is automatically established.	&#x000A;&#x000A;   ```&#x000A;   ./gs_preinstall -U omm -G dbgrp -X /opt/software/ openGauss/clusterconfig.xml&#x000A;   ```&#x000A;&#x000A;   omm is the database administrator (also the OS user running the openGauss), dbgrp is the group name of the OS user running the openGauss, and /opt/software/ openGauss/clusterconfig.xml is the path of the openGauss configuration file. During the execution, you need to determine whether to establish mutual trust as prompted and enter the password of user root or the openGauss user.&#x000A;&#x000A;### Executing Installation&#x000A;&#x000A;After the openGauss installation environment is prepared by executing the pre-installation script, deploy openGauss based on the installation process.&#x000A;**Prerequisites**&#x000A;&#x000A;- You have successfully executed the gs_preinstall script. &#x000A;- All the server OSs and networks are functioning properly.&#x000A;- You have checked that the locale parameter for each server is set to the same value. &#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. (Optional) Check whether the installation package and openGauss configuration file exist in the planned directories. If no such package or file exists, perform the preinstallation again..&#x000A;&#x000A;2. Log in to any host of the openGauss and switch to the omm user.&#x000A;&#x000A;   ```&#x000A;   su - omm&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTE:** &#x000A;   &gt;&#x000A;   &gt; - omm indicates the user specified by the -U parameter in the gs_preinstall script.&#x000A;   &gt; - You need to execute the gs_install script as user omm specified in the gs_preinstall script. Otherwise, an execution error will be reported.&#x000A;&#x000A;3. Use gs_install to install the openGauss. If the openGauss is installed in environment variable separation mode, run the source command to obtain the environment variable separation file ENVFILE.&#x000A;&#x000A;   ```&#x000A;   gs_install -X /opt/software/ openGauss/clusterconfig.xml&#x000A;   ```&#x000A;&#x000A;   The password must meet the following complexity requirements:&#x000A;&#x000A;   - Contain at least eight characters.	&#x000A;   - Cannot be the same as the username, the current password (ALTER), or the current password in an inverted sequence.&#x000A;   - Contain at least three of the following: uppercase characters (A to Z), lowercase characters (a to z), digits (0 to 9), and other characters (limited to ~!@#$%^&amp;*()-_=+\|[{}];:,&lt;.&gt;/?).&#x000A;&#x000A;4. After the installation is successful, manually delete the trust between users root on the host, that is, delete the mutual trust file on each openGauss database node.&#x000A;&#x000A;   ```&#x000A;   rm –rf ~/.ssh&#x000A;   ```&#x000A;&#x000A;### Uninstalling the openGauss&#x000A;&#x000A;The process of uninstalling the openGauss includes uninstalling the openGauss and clearing the environment of the openGauss server.↵&#x000A;&#x000A;##### **Executing Uninstallation**&#x000A;&#x000A;The openGauss provides an uninstallation script to help users uninstall the openGauss.&#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. Log in as the OS user omm to the host where the CN is located.&#x000A;&#x000A;2. Execute the gs_uninstall script to uninstall the database cluster.&#x000A;&#x000A;   ```&#x000A;   gs_uninstall --delete-data&#x000A;   ```&#x000A;&#x000A;   Alternatively, execute uninstallation on each openGauss node.&#x000A;&#x000A;   ```&#x000A;   gs_uninstall --delete-data -L&#x000A;   ```&#x000A;&#x000A;##### **Deleting openGauss Configurations**&#x000A;&#x000A;After the openGauss is uninstalled, execute the gs_postuninstall script to delete configurations from all servers in the openGauss if you do not need to re-deploy the openGauss using these configurations. These configurations are made by the gs_preinstall script.&#x000A;**Prerequisites**&#x000A;&#x000A;- The openGauss uninstallation task has been successfully executed.&#x000A;- User root is trustworthy and available.&#x000A;- Only user root is authorized to run the gs_postuninstall command.&#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. Log in to the openGauss server as user root.&#x000A;&#x000A;2. Run the ssh Host name command to check whether mutual trust has been successfully established. Then, enter exit.&#x000A;&#x000A;   ```&#x000A;   plat1:~ # ssh plat2 &#x000A;   Last login: Tue Jan  5 10:28:18 2016 from plat1 &#x000A;   plat2:~ # exit &#x000A;   logout &#x000A;   Connection to plat2 closed. &#x000A;   plat1:~ #&#x000A;   ```&#x000A;&#x000A;3. Go to the following path:&#x000A;&#x000A;   ```&#x000A;   cd /opt/software/openGauss/script&#x000A;   ```&#x000A;&#x000A;4. Run the gs_postuninstall command to clear the environment. If the openGauss is installed in environment variable separation mode, run the source command to obtain the environment variable separation file ENVFILE.&#x000A;&#x000A;   ```&#x000A;   ./gs_postuninstall -U omm -X /opt/software/openGauss/clusterconfig.xml --delete-user --delete-group&#x000A;   ```&#x000A;&#x000A;   Alternatively, locally use the gs_postuninstall tool to clear each openGauss node.&#x000A;&#x000A;   ```&#x000A;   ./gs_postuninstall -U omm -X /opt/software/openGauss/clusterconfig.xml --delete-user --delete-group -L&#x000A;   ```&#x000A;&#x000A;   omm is the name of the OS user who runs the openGauss, and the path of the openGauss configuration file is /opt/software/openGauss/clusterconfig.xml.&#x000A;   If the cluster is installed in environment variable separation mode, delete the environment variable separation parameter ENV obtained by running the source command.&#x000A;&#x000A;   ```&#x000A;   unset MPPDB_ENV_SEPARATE_PATH&#x000A;   ```&#x000A;&#x000A;5. Delete the mutual trust between the users root on each openGauss database node. &#x000A;&#x000A;&#x000A;## Compilation&#x000A;&#x000A;### Overview&#x000A;&#x000A;To compile openGauss, you need two components: openGauss-server and binarylibs.&#x000A;&#x000A;- openGauss-server: main code of openGauss. You can obtain it from the open source community.&#x000A;&#x000A;- binarylibs: third party open source software that openGauss depends on. You can obtain it by compiling the openGauss-third_party code or downloading from the open source community on which we have compiled a copy and uploaded it . The first method will be introduced in the following chapter.&#x000A;&#x000A;Before you compile openGauss，please check the OS and software dependency requirements.&#x000A;&#x000A;You can compile openGauss by build.sh, a one-click shell tool, which we will introduce later, or compile by command. Also, an installation package is produced by build.sh.&#x000A;&#x000A;### OS and Software Dependency Requirements&#x000A;&#x000A;The following OSs are supported:&#x000A;&#x000A;- CentOS 7.6 (x86 architecture)&#x000A;&#x000A;- openEuler-20.03-LTS (aarch64 architecture)&#x000A;&#x000A;- openEuler-20.03-LTS (x86_64 architecture)&#x000A;&#x000A;- openEuler-22.03-LTS (aarch64 architecture)&#x000A;&#x000A;- openEuler-22.03-LTS (x86_64 architecture)&#x000A;  &#x000A;- openEuler-24.03-LTS (aarch64 architecture)&#x000A;&#x000A;- openEuler-24.03-LTS (x86_64 architecture)&#x000A;&#x000A;&#x000A;The following table lists the software requirements for compiling the openGauss.&#x000A;&#x000A;You are advised to use the default installation packages of the following dependent software in the listed OS installation CD-ROMs or sources. If the following software does not exist, refer to the recommended versions of the software.&#x000A;&#x000A;Software dependency requirements are as follows:&#x000A;&#x000A;| Software      | Recommended Version |&#x000A;| ------------- | ------------------- |&#x000A;| libaio-devel  | 0.3.109-13          |&#x000A;| flex          | 2.5.31 or later     |&#x000A;| bison         | 2.7-4               |&#x000A;| ncurses-devel | 5.9-13.20130511     |&#x000A;| glibc-devel   | 2.17-111            |&#x000A;| patch         | 2.7.1-10            |&#x000A;| lsb_release   | 4.1                 |&#x000A;&#x000A;### Downloading openGauss&#x000A;&#x000A;You can download openGauss-server and openGauss-third_party from open source community.&#x000A;&#x000A;https://opengauss.org/zh/&#x000A;&#x000A;From the following website, you can obtain the binarylibs we have compiled. Please unzip it and rename to **binarylibs** after you download.&#x000A;&#x000A;https://opengauss.obs.cn-south-1.myhuaweicloud.com/2.1.0/openGauss-third_party_binarylibs.tar.gz&#x000A;&#x000A;&#x000A;Now we have completed openGauss code, for example, we store it in following directories.&#x000A;&#x000A;- /sda/openGauss-server&#x000A;- /sda/binarylibs&#x000A;- /sda/openGauss-third_party&#x000A;&#x000A;### Compiling Third-Party Software&#x000A;&#x000A;Before compiling the openGauss, compile and build the open-source and third-party software on which the openGauss depends. These open-source and third-party software is stored in the openGauss-third_party code repository and usually needs to be built only once. If the open-source software is updated, rebuild the software.&#x000A;&#x000A;You can also directly obtain the output file of the open-source software compilation and build from the **binarylibs** repository.&#x000A;&#x000A;If you want to compile third-party by yourself, please go to openGauss-third_party repository to see details. &#x000A;&#x000A;After the preceding script is executed, the final compilation and build result is stored in the **binarylibs** directory at the same level as **openGauss-third_party**. These files will be used during the compilation of **openGauss-server**.&#x000A;&#x000A;### Compiling by build.sh&#x000A;&#x000A;build.sh in openGauss-server is an important script tool during compilation. It integrates software installation and compilation and product installation package compilation functions to quickly compile and package code.&#x000A;&#x000A;The following table describes the parameters.&#x000A;&#x000A;| Option | Default Value                | Parameter                      | Description                              |&#x000A;| :----- | :--------------------------- | :----------------------------- | :--------------------------------------- |&#x000A;| -h     | Do not use this option.      | -                              | Help menu.                               |&#x000A;| -m     | release                      | [debug \| release \| memcheck] | Selects the target version.              |&#x000A;| -3rd   | ${Code directory}/binarylibs | [binarylibs path]              | Specifies the path of binarylibs. The path must be an absolute path. |&#x000A;| -pkg   | Do not use this option.      | -                              | Compresses the code compilation result into an installation package. |&#x000A;&#x000A;&gt; **NOTICE:** &#x000A;&gt;&#x000A;&gt; 1. **-m [debug | release | memcheck]** indicates that three target versions can be selected:&#x000A;&gt;    - **release**: indicates that the binary program of the release version is generated. During compilation of this version, the GCC high-level optimization option is configured to remove the kernel debugging code. This option is usually used in the generation environment or performance test environment.&#x000A;&gt;    - **debug**: indicates that a binary program of the debug version is generated. During compilation of this version, the kernel code debugging function is added, which is usually used in the development self-test environment.&#x000A;&gt;    - **memcheck**: indicates that a binary program of the memcheck version is generated. During compilation of this version, the ASAN function is added based on the debug version to locate memory problems.&#x000A;&gt; 2. **-3rd [binarylibs path]** is the path of **binarylibs**. By default, **binarylibs** exists in the current code folder. If **binarylibs** is moved to **openGauss-server** or a soft link to **binarylibs** is created in **openGauss-server**, you do not need to specify the parameter. However, if you do so, please note that the file is easy to be deleted by the **git clean** command.&#x000A;&gt; 3. Each option in this script has a default value. The number of options is small and the dependency is simple. Therefore, this script is easy to use. If the required value is different from the default value, set this parameter based on the actual requirements.&#x000A;&#x000A;Now you know the usage of build.sh, so you can compile the openGauss-server by one command with build.sh.&#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh -m [debug | release | memcheck] -3rd [binarylibs path]&#x000A;```&#x000A;&#x000A;For example: &#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh       # Compile openGauss of the release version. The binarylibs or its soft link must exist in the code directory. Otherwise, the operation fails.&#x000A;[user@linux openGauss-server]$ sh build.sh -m debug -3rd /sda/binarylibs    # Compilate openGauss of the debug version using binarylibs we put on /sda/&#x000A;```&#x000A;&#x000A;The software installation path after compilation is **/sda/openGauss-server/dest**.&#x000A;&#x000A;The compiled binary files are stored in **/sda/openGauss-server/dest/bin**.&#x000A;&#x000A;Compilation log: **make_compile.log**&#x000A;&#x000A;&#x000A;&#x000A;### Compiling by Command&#x000A;&#x000A;1. Run the following script to obtain the system version:&#x000A;&#x000A;   ```&#x000A;   [user@linux openGauss-server]$ sh src/get_PlatForm_str.sh&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTICE:** &#x000A;   &gt;&#x000A;   &gt; - The command output indicates the OSs supported by the openGauss. The OSs supported by the openGauss are centos7.6_x86_64 and openeuler_aarch64.&#x000A;   &gt; - If **Failed** or another version is displayed, the openGauss does not support the current operating system.&#x000A;&#x000A;2. Configure environment variables, add **____** based on the code download location, and replace *** with the result obtained in the previous step.&#x000A;&#x000A;   ```&#x000A;   export CODE_BASE=________     # Path of the openGauss-server file&#x000A;   export BINARYLIBS=________    # Path of the binarylibs file&#x000A;   export GAUSSHOME=$CODE_BASE/dest/&#x000A;   export GCC_PATH=$BINARYLIBS/buildtools/***/gcc7.3/&#x000A;   export CC=$GCC_PATH/gcc/bin/gccexport CXX=$GCC_PATH/gcc/bin/g++&#x000A;   export LD_LIBRARY_PATH=$GAUSSHOME/lib:$GCC_PATH/gcc/lib64:$GCC_PATH/isl/lib:$GCC_PATH/mpc/lib/:$GCC_PATH/mpfr/lib/:$GCC_PATH/gmp/lib/:$LD_LIBRARY_PATH&#x000A;   export PATH=$GAUSSHOME/bin:$GCC_PATH/gcc/bin:$PATH&#x000A;&#x000A;   ```&#x000A;&#x000A;3. Select a version and configure it.&#x000A;&#x000A;   **debug** version:&#x000A;&#x000A;   ```&#x000A;   ./configure --gcc-version=7.3.0 CC=g++ CFLAGS=&#39;-O0&#39; --prefix=$GAUSSHOME --3rd=$BINARYLIBS --enable-debug --enable-cassert --enable-thread-safety --without-readline --without-zlib&#x000A;   ```&#x000A;&#x000A;   **release** version:&#x000A;&#x000A;   ```&#x000A;   ./configure --gcc-version=7.3.0 CC=g++ CFLAGS=&quot;-O2 -g3&quot; --prefix=$GAUSSHOME --3rd=$BINARYLIBS --enable-thread-safety --without-readline --without-zlib&#x000A;   ```&#x000A;&#x000A;   **memcheck** version:&#x000A;&#x000A;   ```&#x000A;   ./configure --gcc-version=7.3.0 CC=g++ CFLAGS=&#39;-O0&#39; --prefix=$GAUSSHOME --3rd=$BINARYLIBS --enable-debug --enable-cassert --enable-thread-safety --without-readline --without-zlib --enable-memory-check&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTICE:** &#x000A;   &gt;&#x000A;   &gt; 1. *[debug | release | memcheck]* indicates that three target versions are available. &#x000A;   &gt; 2. On the ARM-based platform, **-D__USE_NUMA** needs to be added to **CFLAGS**.&#x000A;   &gt; 3. On the **ARMv8.1** platform or a later version (for example, Kunpeng 920), **-D__ARM_LSE** needs to be added to **CFLAGS**.&#x000A;   &gt; 4. If **binarylibs** is moved to **openGauss-server** or a soft link to **binarylibs** is created in **openGauss-server**, you do not need to specify the **--3rd** parameter. However, if you do so, please note that the file is easy to be deleted by the `git clean` command.&#x000A;   &gt; 5. To build with mysql_fdw, add **--enable-mysql-fdw** when configure. Note that before build mysql_fdw, MariaDB&#39;s C client library is needed.&#x000A;   &gt; 6. To build with oracle_fdw, add **--enable-oracle-fdw** when configure. Note that before build oracle_fdw, Oracle&#39;s C client library is needed.&#x000A;&#x000A;4. Run the following commands to compile openGauss:&#x000A;&#x000A;   ```&#x000A;   [user@linux openGauss-server]$ make -sj&#x000A;   [user@linux openGauss-server]$ make install -sj&#x000A;   ```&#x000A;&#x000A;5. If the following information is displayed, the compilation and installation are successful:&#x000A;&#x000A;   ```&#x000A;   openGauss installation complete.&#x000A;   ```&#x000A;&#x000A;   The software installation path after compilation is **$GAUSSHOME**.&#x000A;&#x000A;   The compiled binary files are stored in **$GAUSSHOME/bin**.&#x000A;&#x000A;&#x000A;&#x000A;### Compiling the Installation Package &#x000A;&#x000A;Please read the chapter **Compiling by build.sh** first to understand the usage of build.sh and how to compile openGauss by using the script.&#x000A;&#x000A;Now you can compile the installation package with just adding a option `-pkg`.&#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh -m [debug | release | memcheck] -3rd [binarylibs path] -pkg&#x000A;```&#x000A;&#x000A;For example:&#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh -pkg      # Compile openGauss installation package of the release version. The binarylibs or its soft link must exist in the code directory. Otherwise, the operation fails.&#x000A;[user@linux openGauss-server]$ sh build.sh -m debug -3rd /sda/binarylibs -pkg   # Compile openGauss installation package of the debug version using binarylibs we put on /sda/&#x000A;```&#x000A;&#x000A;The generated installation package is stored in the **./package** directory.&#x000A;&#x000A;Compilation log: **make_compile.log**&#x000A;&#x000A;Installation package packaging log: **./package/make_package.log**&#x000A;&#x000A;## Quick Start&#x000A;&#x000A;See the [Quick Start](https://opengauss.org/zh/docs/2.1.0/docs/Quickstart/Quickstart.html) to implement the image classification.&#x000A;&#x000A;## Docs&#x000A;&#x000A;For more details about the installation guide, tutorials, and APIs, please see the [User Documentation](https://gitcode.com/opengauss/docs).&#x000A;&#x000A;## Community&#x000A;&#x000A;### Governance&#x000A;&#x000A;Check out how openGauss implements open governance [works](https://gitcode.com/opengauss/community/blob/master/governance.md).&#x000A;&#x000A;### Communication&#x000A;&#x000A;- WeLink- Communication platform for developers.&#x000A;- IRC channel at `#opengauss-meeting` (only for meeting minutes logging purpose)&#x000A;- Mailing-list: &lt;https://opengauss.org/zh/community/onlineCommunication/&gt;&#x000A;&#x000A;## Contribution&#x000A;&#x000A;Welcome contributions. See our [Contributor](https://opengauss.org/en/contribution/) for more details.&#x000A;&#x000A;## Release Notes&#x000A;&#x000A;For the release notes, see our [RELEASE](https://opengauss.org/zh/docs/2.1.0/docs/Releasenotes/Releasenotes.html).&#x000A;&#x000A;## License&#x000A;&#x000A;[MulanPSL-2.0](http://license.coscl.org.cn/MulanPSL2)&#x000A;</textarea>
<a class="ui button" id="copy-text" href="#">Copy</a>
<a class="ui button edit-blob" title="Please login" href="/opengauss/openGauss-server/edit/master/README.en.md">Edit</a>
<a class="ui button edit-raw" target="_blank" href="https://gitee.com/opengauss/openGauss-server/raw/master/README.en.md">Raw</a>
<a class="ui button edit-blame" href="/opengauss/openGauss-server/blame/master/README.en.md">Blame</a>
<a class="ui button edit-history" href="/opengauss/openGauss-server/commits/master/README.en.md">History</a>
</div>
<script>
  window.gon.aiCodeParams = {
    // pathWithNamespace: `opengauss/openGauss-server`,
    // fileName: `README.en.md`,
    // id: `76cc566a3c7e851497534631e48e720d0684312e`,
    // timeStamp: `1774149802`,
    // sign: `i5fBfcWoBXbLv/ApFfTRTTTtlOTppbXOoKsHO5RmQSk2wBPpH3/xL5RS/Mu/BhOci6OtfdzqGCiyVVlOkLHOta00Pu3/BrRNvqJ5/rCHETOfaAMqAxR4ZWs2XV73geOQ`,
    blob:  $("#blob_raw").val(),
    type: "code",
    user: ``,
  }
  
  window.gon.blobName = `"README.en.md"`
  $('.js-code-parsing').dropdown({
    on: 'hover',
    action: 'hide',
    onHide: function () {
    },
    onShow: function () {
    }
  });
  $(".ai-code-dropdown-box").find('.item').on("click", function (e) {
    window.jqxhr && window.jqxhr.abort();
    window.aiLoadingTimer && clearTimeout(window.aiLoadingTimer);
    aiReqLoading = false
  
    window.Gitee.setFullscreen(true);
    $(".side-toolbar").hide();
    var $siteContent = $(".site-content");
    // 获取最小高度
    var minHeight = parseInt($siteContent.css("min-height"));
    // 获取当前高度
    var currentHeight = parseInt($siteContent.height());
    if (minHeight + 1 > currentHeight) {
      $("#code-parsing").css("height", currentHeight);
    }
  
    $("#git-project-container").addClass('git-transition-width');
    $("#project-wrapper").css("marginTop", "-24px");
    //$("#git-project-container").removeClass("sixteen wide column");
    //$("#git-project-container").addClass("twelve wide column");
    if(!$("#code-parsing").hasClass("code-parsing-box")){
      $("#git-project-container").attr("style", "width: 75% !important;");
      $('.git-project-content-wrapper').find('#sixteen').attr("style", "width: 75% !important;");
      $('.right-wrapper').attr("style", "width: 75% !important;");
      $('.project-conter-container').attr("style", "width: 75% !important;");
    }
    $("#git-footer-main").css("margin-top", "14px");
    $("#code-parsing").addClass("code-parsing-box");
    // 当详情页宽度不够存放文件树时候隐藏
    var containerWidth = $("#project-wrapper").width();
    if (containerWidth < 1450) {
      $('.project-left-side-contaner').hide();
      $('#file-iconify-wrapper').removeClass('hide')
    }
  
    $(".code-parsing-content").hide();
    $(".skeleton").show();
    $(".ai_code_btns_simple").hide();
  
    $("#code-parsing").find(".markdown-body").innerHTML='';
  
    aiCodeType = $(this).data("value");
    aiSubTitle = $(this).data("text");
    handleAiReqInit()
  });
</script>
<script>
  "use strict";
  try {
    if((gon.wait_fork!=undefined && gon.wait_fork==true) || (gon.wait_fetch!=undefined && gon.wait_fetch==true)){
      $('.edit-blob').popup({content:"This repository is doing something background, pleace try again later", on: 'hover', delay: { show: 200, hide: 200 }});
      $('.edit-blob').click(function(e){
        e.preventDefault();
      })
    }
  
    var setUrl = function() {
      var params = window.location.search
      if (params==undefined || $.trim(params).length==0) return;
      $('span.options').children('.basic').find('a').each(function(index,ele){
        var origin_href = $(ele).attr('href');
        if (origin_href!="#" && origin_href.indexOf('?') == -1){
          $(ele).attr('href',origin_href+params);
        }
      });
    }
  
    setUrl();
  
    var clipboard = null,
        $btncopy  = $("#copy-text");
  
    clipboard = new Clipboard("#copy-text", {
      text: function(trigger) {
        return $("#blob_raw").val();
      }
    })
  
    clipboard.on('success', function(e) {
      $btncopy.popup('hide');
      $btncopy.popup('destroy');
      $btncopy.popup({content: 'Copied', position: 'bottom center'});
      $btncopy.popup('show');
    })
  
    clipboard.on('error', function(e) {
      var giteeModal = new GiteeModalHelper({okText: 'Confirm'});
      giteeModal.alert("Copy", 'Copy failed. Please copy it manually');
    })
  
    $(function() {
      $btncopy.popup({
        content: 'Copy to clipboard',
        position: 'bottom center'
      })
    })
  
  } catch (error) {
    console.log('blob/action error:' + error);
  }
  
  $(".disabled-edit-readonly").popup({
    content: "Readonly file is not editable",
    className: {
      popup: "ui popup",
    },
    position: "bottom center",
  });
  $(".disabled-edit-readonly, .disabled-edit-status").click(function () {
    return false;
  });
  $(".has_tooltip").popup({
    position: "top center",
  });
  window.onload = window.Gitee.aiAssistant.checkAIAssistantExpire
</script>
<style>
  .disabled-edit-readonly, .disabled-edit-status {
    background-color: #dcddde !important;
    color: rgba(0, 0, 0, 0.4) !important;
    opacity: 0.3 !important;
    background-image: none !important;
    -webkit-box-shadow: none !important;
            box-shadow: none !important;
    cursor: default !important; }
  
  .drawio-iframe-code-card {
    position: relative; }
    .drawio-iframe-code-card textarea {
      width: 100%;
      height: 140px;
      resize: none; }
    .drawio-iframe-code-card .icon-clone {
      position: absolute;
      right: 32px;
      bottom: 32px; }
    .drawio-iframe-code-card iframe {
      border-radius: 2px;
      border: 1px solid #DEDEDF; }
</style>
</div>
</div>
<div class='blob-header-title mt-1 ubblock_tip'>
</div>
<div class='contributor-description'><span class='recent-commit' style='margin-top: 0.7rem'>
<a class="commit-author-link  js-popover-card " data-username="yaaaaali" href="/yaaaaali">yaaaaali</a>
<span>authored</span>
<span class='timeago commit-date' title='2025-07-24 20:18 +08:00'>
2025-07-24 20:18 +08:00
</span>
.
<a href="/opengauss/openGauss-server/commit/136cb64fb7ae07c01a6432537fb2b444154495ce">修改文档错误信息</a>
</span>
</div>
</div>
<div class='clearfix'></div>
<div class='file_catalog'>
<div class='toggle'>
<i class='icon angle left'></i>
</div>
<div class='scroll-container'>
<div class='container'>
<div class='skeleton'>
<div class='line line1'></div>
<div class='line line2'></div>
<div class='line line3'></div>
<div class='line line1'></div>
<div class='line line2'></div>
<div class='line line3'></div>
</div>
</div>
</div>
</div>
<div class='file_content markdown-body'>
<blob-markdown-renderer data-dir='' data-path-with-namespace='/opengauss/openGauss-server'>&#x000A;<textarea class='content' style='display:none;'>![openGauss Logo](doc/openGauss-logo.png &quot;openGauss logo&quot;)&#x000A;============================================================&#x000A;&#x000A;- [What Is openGauss?](#What Is openGauss?)&#x000A;- [Installation](#Installation)&#x000A;    - [Creating a Configuration File](#Creating a Configuration File)&#x000A;    - [Initializing the Installation Environment](#Initializing the Installation Environment)&#x000A;- [Executing Installation](#Executing Installation)&#x000A;  [Uninstalling the openGauss](#Uninstalling the openGauss)&#x000A;- [Compilation](#Compilation)&#x000A;    - [Overview](#Overview)&#x000A;    - [OS and Software Dependency Requirements](# OS and Software Dependency Requirements)&#x000A;    - [Downloading openGauss](# Downloading openGauss)&#x000A;    - [Compiling Third-Party Software](#Compiling Third-Party Software)&#x000A;    - [Compiling by build.sh](#Compiling by build.sh)&#x000A;    - [Compiling by Command](#Compiling by Command)&#x000A;    - [Compiling the Installation Package](#Compiling the Installation Package)&#x000A;- [Quick Start](#Quick Start)&#x000A;- [Docs](#Docs)&#x000A;- [Community](#Community)&#x000A;    - [Governance](#Governance)&#x000A;    - [Communication](#Communication)&#x000A;- [Contribution](#Contribution)&#x000A;- [Release Notes](#Release Notes)&#x000A;- [License](#License)&#x000A;&#x000A;## What Is openGauss?&#x000A;&#x000A;openGauss is an open source relational database management system. It has multi-core high-performance, full link security, intelligent operation and maintenance for enterprise features. openGauss integrates Huawei's core experience in database field for many years. It optimizes the architecture, transaction, storage engine, optimizer and ARM architecture. At the meantime, openGauss as a global database open source community, aims to further advance the development and enrichment of the database software/hardware application ecosystem.&#x000A;&#x000A;&lt;img src=&quot;doc/openGauss-architecture.png&quot; alt=&quot;opengauss Architecture&quot; width=&quot;600&quot;/&gt;&#x000A;&#x000A;**High Performance**&#x000A;&#x000A;openGauss breaks through the bottleneck of multi-core CPU, 2-way Kunpeng 128 core 1.5 million TPMC.&#x000A;&#x000A;**Partitions**&#x000A;&#x000A;Divide key data structure shared by internal threads into different partitions to reduce lock access conflicts. For example, CLOG uses partition optimization to solve the bottleneck of ClogControlLock.&#x000A;&#x000A;**NUMA Structure**&#x000A;&#x000A;Malloc key data structures help reduce cross CPU access. The global PGPROC array is divided into several parts according to the number of NUMA nodes, solving the bottleneck of ProcArrayLock. &#x000A;&#x000A;**Binding Cores**&#x000A;&#x000A;Bind NIC interrupts to different cores and bind cores to different background threads to avoid performance instability due to thread migration between cores.&#x000A;&#x000A;**ARM Optimization**&#x000A;&#x000A;Optimize atomic operations based on ARM platform LSE instructions, impletmenting efficient operation of critical sections.&#x000A;&#x000A;**SQL Bypass**&#x000A;&#x000A;Optimize SQL execution process through SQL bypass, reducing CPU execution overhead.&#x000A;&#x000A;**High Reliability**&#x000A;&#x000A;Under normal service loads, the RTO is less than 10 seconds, reducing the service interruption time caused by node failure.&#x000A;&#x000A;**Parallel Recovery**&#x000A;&#x000A;When the Xlog is transferred to the standby node, the standby node flushs the Xlog to storage medium. At the mean time, the Xlog is sent to the redo recovery dispatch thread. The dispatch thread sends the Xlog to multiple parallel recovery threads to replay. Ensure that the redo speed of the standby node keeps up with the generation speed of the primary host. The standby node is ready in real time, which can be promoted to primary instantly. &#x000A;&#x000A;**MOT Engine (beta release)**&#x000A;&#x000A;The Memory-Optimized Tables (MOT) storage engine is a transactional rowstore optimized for many-core and large memory and delivering extreme OLTP performance and high resources utilization. With data and indexes stored totally in-memory, a NUMA-aware design, algorithms that eliminate lock and latch contention and query native compilation (JIT), MOT provides low latency data access and more efficient transaction execution. See [MOT Engine documentation](https://opengauss.org/en/docs/2.1.0/docs/Developerguide/mot.html).&#x000A;&#x000A;**Security**&#x000A;&#x000A;openGauss supports account management, account authentication, account locking, password complexity check, privilege management and verification, transmission encryption, and operation audit, protecting service data security.&#x000A;&#x000A;**Easy Operation and Maintenance**&#x000A;&#x000A;openGauss integrates AI algorithms into databases, reducing the burden of database maintenance.&#x000A;&#x000A;- **SQL Prediction**&#x000A;&#x000A;openGauss supports SQL execution time prediction based on collected historical performance data.&#x000A;&#x000A;- **SQL Diagnoser **&#x000A;&#x000A;openGauss supports the diagnoser for SQL execution statements, finding out slow queries in advance..&#x000A;&#x000A;- **Automatical Parameter Adjustment**&#x000A;&#x000A;openGauss supports automatically adjusting database parameters, reducing the cost and time of parameter adjustment.&#x000A;&#x000A;## Installation&#x000A;&#x000A;### Creating a Configuration File&#x000A;&#x000A;Before installing the openGauss, you need to create a configuration file. The configuration file in the XML format contains the information about the server where the openGauss is deployed, installation path, IP address, and port number. This file is used to guide how to deploy the openGauss. You need to configure the configuration file according to the actual deployment requirements.&#x000A;&#x000A;The following describes how to create an XML configuration file based on the deployment solution of one primary node and one standby node.&#x000A;The information in bold is only an example. You can replace it as required. Each line of information is commented out.&#x000A;&#x000A;```&#x000A;&lt;?xml version=&quot;1.0&quot; encoding=&quot;utf-8&quot;?&gt;&#x000A;&lt;ROOT&gt;&#x000A;&lt;!-- Overall information --&gt;&#x000A;  &lt;CLUSTER&gt;&#x000A;  &lt;!-- Database name --&gt;&#x000A;    &lt;PARAM name=&quot;clusterName&quot; value=&quot;Cluster_template&quot; /&gt;&#x000A;	&lt;!-- Database node name (hostname) --&gt;&#x000A;    &lt;PARAM name=&quot;nodeNames&quot; value=&quot;node1_hostname,node2_hostname&quot;/&gt;&#x000A;	&lt;!-- Database installation path --&gt;&#x000A;    &lt;PARAM name=&quot;gaussdbAppPath&quot; value=&quot;/opt/huawei/install/app&quot; /&gt;&#x000A;	&lt;!-- Log directory --&gt;&#x000A;    &lt;PARAM name=&quot;gaussdbLogPath&quot; value=&quot;/var/log/omm&quot; /&gt;&#x000A;	&lt;!-- Temporary file directory --&gt;&#x000A;    &lt;PARAM name=&quot;tmpMppdbPath&quot; value=&quot;/opt/huawei/tmp&quot;/&gt;&#x000A;	&lt;!-- Database tool directory --&gt;&#x000A;    &lt;PARAM name=&quot;gaussdbToolPath&quot; value=&quot;/opt/huawei/install/om&quot; /&gt;&#x000A;	&lt;!--Directory of the core file of the database --&gt;&#x000A;    &lt;PARAM name=&quot;corePath&quot; value=&quot;/opt/huawei/corefile&quot;/&gt;&#x000A;	&lt;!-- Node IP addresses corresponding to the node names, respectively --&gt;&#x000A;    &lt;PARAM name=&quot;backIp1s&quot; value=&quot;192.168.0.1,192.168.0.2&quot;/&gt;&#x000A;  &lt;/CLUSTER&gt;&#x000A;&lt;!-- Information about node deployment on each server --&gt;&#x000A;  &lt;DEVICELIST&gt;&#x000A;  &lt;!-- Information about the node deployment on node1 --&gt;&#x000A;    &lt;DEVICE sn=&quot;node1_hostname&quot;&gt;&#x000A;	  &lt;!-- Host name of node1 --&gt;&#x000A;      &lt;PARAM name=&quot;name&quot; value=&quot;node1_hostname&quot;/&gt;&#x000A;	  &lt;!-- AZ where node1 is located and AZ priority --&gt;&#x000A;      &lt;PARAM name=&quot;azName&quot; value=&quot;AZ1&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;azPriority&quot; value=&quot;1&quot;/&gt;&#x000A;	  &lt;!-- IP address of node1. If only one NIC is available for the server, set backIP1 and sshIP1 to the same IP address. --&gt;&#x000A;      &lt;PARAM name=&quot;backIp1&quot; value=&quot;192.168.0.1&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;sshIp1&quot; value=&quot;192.168.0.1&quot;/&gt;&#x000A;      &lt;!--DBnode--&gt;&#x000A;      &lt;PARAM name=&quot;dataNum&quot; value=&quot;1&quot;/&gt;&#x000A;	  &lt;!-- Database node port number --&gt;&#x000A;      &lt;PARAM name=&quot;dataPortBase&quot; value=&quot;15400&quot;/&gt;&#x000A;	  &lt;!-- Data directory on the primary database node and data directories of standby nodes --&gt;&#x000A;      &lt;PARAM name=&quot;dataNode1&quot; value=&quot;/opt/huawei/install/data/dn,node2_hostname,/opt/huawei/install/data/dn&quot;/&gt;&#x000A;	  &lt;!-- Number of nodes for which the synchronization mode is set on the database node --&gt;&#x000A;      &lt;PARAM name=&quot;dataNode1_syncNum&quot; value=&quot;0&quot;/&gt;&#x000A;    &lt;/DEVICE&gt;&#x000A;  &lt;!-- Information about the node deployment on node2 --&gt;&#x000A;    &lt;DEVICE sn=&quot;node2_hostname&quot;&gt;&#x000A;	  &lt;!-- Host name of node2 --&gt;&#x000A;      &lt;PARAM name=&quot;name&quot; value=&quot;node2_hostname&quot;/&gt;&#x000A;	  &lt;!-- AZ where node1 is located and AZ priority --&gt;&#x000A;      &lt;PARAM name=&quot;azName&quot; value=&quot;AZ1&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;azPriority&quot; value=&quot;1&quot;/&gt;&#x000A;	  &lt;!-- IP address of node1. If only one NIC is available for the server, set backIP1 and sshIP1 to the same IP address. --&gt;&#x000A;      &lt;PARAM name=&quot;backIp1&quot; value=&quot;192.168.0.2&quot;/&gt;&#x000A;      &lt;PARAM name=&quot;sshIp1&quot; value=&quot;192.168.0.2&quot;/&gt;&#x000A;    &lt;/DEVICE&gt;&#x000A;  &lt;/DEVICELIST&gt;&#x000A;&lt;/ROOT&gt;&#x000A;```&#x000A;&#x000A;### Initializing the Installation Environment&#x000A;&#x000A;After the openGauss configuration file is created, you need to run the gs_preinstall script to prepare the account and environment so that you can perform openGauss installation and management operations with the minimum permission, ensuring system security.&#x000A;&#x000A;**Precautions**&#x000A;&#x000A;- You must check the upper-layer directory permissions to ensure that the user has the read, write, and execution permissions on the installation package and configuration file directory.&#x000A;- The mapping between each host name and IP address in the XML configuration file must be correct.&#x000A;- Only user root is authorized to run the gs_preinstall command.&#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. Log in to any host where the openGauss is to be installed as user root and create a directory for storing the installation package as planned.&#x000A;&#x000A;   ```&#x000A;   mkdir -p /opt/software/openGauss&#x000A;   chmod 755 -R /opt/software&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTE:** &#x000A;   &gt;&#x000A;   &gt; - Do not create the directory in the home directory or subdirectory of any openGauss user because you may lack permissions for such directories.&#x000A;   &gt; - The openGauss user must have the read and write permissions on the /opt/software/openGauss directory.&#x000A;&#x000A;2. The release package is used as an example. Upload the installation package openGauss_x.x.x_PACKAGES_RELEASE.tar.gz and the configuration file clusterconfig.xml to the directory created in the previous step.&#x000A;&#x000A;3. Go to the directory for storing the uploaded software package and decompress the package.&#x000A;&#x000A;   ```&#x000A;   cd /opt/software/openGauss&#x000A;   tar -zxvf openGauss_x.x.x_PACKAGES_RELEASE.tar.gz&#x000A;   ```&#x000A;&#x000A;4. Decompress the openGauss-x.x.x-openEULER-64bit.tar.gz package.&#x000A;&#x000A;   ```&#x000A;   tar -zxvf openGauss-x.x.x-openEULER-64bit.tar.gz&#x000A;   ```&#x000A;&#x000A;   After the installation package is decompressed, the script subdirectory is automatically generated in /opt/software/openGauss. OM tool scripts such as gs_preinstall are generated in the script subdirectory.&#x000A;&#x000A;5. Go to the directory for storing tool scripts.&#x000A;&#x000A;   ```&#x000A;   cd /opt/software/openGauss/script&#x000A;   ```&#x000A;&#x000A;6. To ensure that the OpenSSL version is correct, load the lib library in the installation package before preinstallation. Run the following command. {packagePath} indicates the path where the installation package is stored. In this example, the path is /opt/software/openGauss.&#x000A;&#x000A;   ```&#x000A;   export LD_LIBRARY_PATH={packagePath}/script/gspylib/clib:$LD_LIBRARY_PATH&#x000A;   ```&#x000A;&#x000A;&#x000A;7. To ensure successful installation, check whether the values of hostname and /etc/hostname are the same. During preinstallation, the host name is checked.&#x000A;&#x000A;8. Execute gs_preinstall to configure the installation environment. If the shared environment is used, add the --sep-env-file=ENVFILE parameter to separate environment variables to avoid mutual impact with other users. The environment variable separation file path is specified by users.&#x000A;   Execute gs_preinstall in interactive mode. During the execution, the mutual trust between users root and between clusteropenGauss users is automatically established.	&#x000A;&#x000A;   ```&#x000A;   ./gs_preinstall -U omm -G dbgrp -X /opt/software/ openGauss/clusterconfig.xml&#x000A;   ```&#x000A;&#x000A;   omm is the database administrator (also the OS user running the openGauss), dbgrp is the group name of the OS user running the openGauss, and /opt/software/ openGauss/clusterconfig.xml is the path of the openGauss configuration file. During the execution, you need to determine whether to establish mutual trust as prompted and enter the password of user root or the openGauss user.&#x000A;&#x000A;### Executing Installation&#x000A;&#x000A;After the openGauss installation environment is prepared by executing the pre-installation script, deploy openGauss based on the installation process.&#x000A;**Prerequisites**&#x000A;&#x000A;- You have successfully executed the gs_preinstall script. &#x000A;- All the server OSs and networks are functioning properly.&#x000A;- You have checked that the locale parameter for each server is set to the same value. &#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. (Optional) Check whether the installation package and openGauss configuration file exist in the planned directories. If no such package or file exists, perform the preinstallation again..&#x000A;&#x000A;2. Log in to any host of the openGauss and switch to the omm user.&#x000A;&#x000A;   ```&#x000A;   su - omm&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTE:** &#x000A;   &gt;&#x000A;   &gt; - omm indicates the user specified by the -U parameter in the gs_preinstall script.&#x000A;   &gt; - You need to execute the gs_install script as user omm specified in the gs_preinstall script. Otherwise, an execution error will be reported.&#x000A;&#x000A;3. Use gs_install to install the openGauss. If the openGauss is installed in environment variable separation mode, run the source command to obtain the environment variable separation file ENVFILE.&#x000A;&#x000A;   ```&#x000A;   gs_install -X /opt/software/ openGauss/clusterconfig.xml&#x000A;   ```&#x000A;&#x000A;   The password must meet the following complexity requirements:&#x000A;&#x000A;   - Contain at least eight characters.	&#x000A;   - Cannot be the same as the username, the current password (ALTER), or the current password in an inverted sequence.&#x000A;   - Contain at least three of the following: uppercase characters (A to Z), lowercase characters (a to z), digits (0 to 9), and other characters (limited to ~!@#$%^&amp;*()-_=+\|[{}];:,&lt;.&gt;/?).&#x000A;&#x000A;4. After the installation is successful, manually delete the trust between users root on the host, that is, delete the mutual trust file on each openGauss database node.&#x000A;&#x000A;   ```&#x000A;   rm –rf ~/.ssh&#x000A;   ```&#x000A;&#x000A;### Uninstalling the openGauss&#x000A;&#x000A;The process of uninstalling the openGauss includes uninstalling the openGauss and clearing the environment of the openGauss server.↵&#x000A;&#x000A;##### **Executing Uninstallation**&#x000A;&#x000A;The openGauss provides an uninstallation script to help users uninstall the openGauss.&#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. Log in as the OS user omm to the host where the CN is located.&#x000A;&#x000A;2. Execute the gs_uninstall script to uninstall the database cluster.&#x000A;&#x000A;   ```&#x000A;   gs_uninstall --delete-data&#x000A;   ```&#x000A;&#x000A;   Alternatively, execute uninstallation on each openGauss node.&#x000A;&#x000A;   ```&#x000A;   gs_uninstall --delete-data -L&#x000A;   ```&#x000A;&#x000A;##### **Deleting openGauss Configurations**&#x000A;&#x000A;After the openGauss is uninstalled, execute the gs_postuninstall script to delete configurations from all servers in the openGauss if you do not need to re-deploy the openGauss using these configurations. These configurations are made by the gs_preinstall script.&#x000A;**Prerequisites**&#x000A;&#x000A;- The openGauss uninstallation task has been successfully executed.&#x000A;- User root is trustworthy and available.&#x000A;- Only user root is authorized to run the gs_postuninstall command.&#x000A;&#x000A;**Procedure**&#x000A;&#x000A;1. Log in to the openGauss server as user root.&#x000A;&#x000A;2. Run the ssh Host name command to check whether mutual trust has been successfully established. Then, enter exit.&#x000A;&#x000A;   ```&#x000A;   plat1:~ # ssh plat2 &#x000A;   Last login: Tue Jan  5 10:28:18 2016 from plat1 &#x000A;   plat2:~ # exit &#x000A;   logout &#x000A;   Connection to plat2 closed. &#x000A;   plat1:~ #&#x000A;   ```&#x000A;&#x000A;3. Go to the following path:&#x000A;&#x000A;   ```&#x000A;   cd /opt/software/openGauss/script&#x000A;   ```&#x000A;&#x000A;4. Run the gs_postuninstall command to clear the environment. If the openGauss is installed in environment variable separation mode, run the source command to obtain the environment variable separation file ENVFILE.&#x000A;&#x000A;   ```&#x000A;   ./gs_postuninstall -U omm -X /opt/software/openGauss/clusterconfig.xml --delete-user --delete-group&#x000A;   ```&#x000A;&#x000A;   Alternatively, locally use the gs_postuninstall tool to clear each openGauss node.&#x000A;&#x000A;   ```&#x000A;   ./gs_postuninstall -U omm -X /opt/software/openGauss/clusterconfig.xml --delete-user --delete-group -L&#x000A;   ```&#x000A;&#x000A;   omm is the name of the OS user who runs the openGauss, and the path of the openGauss configuration file is /opt/software/openGauss/clusterconfig.xml.&#x000A;   If the cluster is installed in environment variable separation mode, delete the environment variable separation parameter ENV obtained by running the source command.&#x000A;&#x000A;   ```&#x000A;   unset MPPDB_ENV_SEPARATE_PATH&#x000A;   ```&#x000A;&#x000A;5. Delete the mutual trust between the users root on each openGauss database node. &#x000A;&#x000A;&#x000A;## Compilation&#x000A;&#x000A;### Overview&#x000A;&#x000A;To compile openGauss, you need two components: openGauss-server and binarylibs.&#x000A;&#x000A;- openGauss-server: main code of openGauss. You can obtain it from the open source community.&#x000A;&#x000A;- binarylibs: third party open source software that openGauss depends on. You can obtain it by compiling the openGauss-third_party code or downloading from the open source community on which we have compiled a copy and uploaded it . The first method will be introduced in the following chapter.&#x000A;&#x000A;Before you compile openGauss，please check the OS and software dependency requirements.&#x000A;&#x000A;You can compile openGauss by build.sh, a one-click shell tool, which we will introduce later, or compile by command. Also, an installation package is produced by build.sh.&#x000A;&#x000A;### OS and Software Dependency Requirements&#x000A;&#x000A;The following OSs are supported:&#x000A;&#x000A;- CentOS 7.6 (x86 architecture)&#x000A;&#x000A;- openEuler-20.03-LTS (aarch64 architecture)&#x000A;&#x000A;- openEuler-20.03-LTS (x86_64 architecture)&#x000A;&#x000A;- openEuler-22.03-LTS (aarch64 architecture)&#x000A;&#x000A;- openEuler-22.03-LTS (x86_64 architecture)&#x000A;  &#x000A;- openEuler-24.03-LTS (aarch64 architecture)&#x000A;&#x000A;- openEuler-24.03-LTS (x86_64 architecture)&#x000A;&#x000A;&#x000A;The following table lists the software requirements for compiling the openGauss.&#x000A;&#x000A;You are advised to use the default installation packages of the following dependent software in the listed OS installation CD-ROMs or sources. If the following software does not exist, refer to the recommended versions of the software.&#x000A;&#x000A;Software dependency requirements are as follows:&#x000A;&#x000A;| Software      | Recommended Version |&#x000A;| ------------- | ------------------- |&#x000A;| libaio-devel  | 0.3.109-13          |&#x000A;| flex          | 2.5.31 or later     |&#x000A;| bison         | 2.7-4               |&#x000A;| ncurses-devel | 5.9-13.20130511     |&#x000A;| glibc-devel   | 2.17-111            |&#x000A;| patch         | 2.7.1-10            |&#x000A;| lsb_release   | 4.1                 |&#x000A;&#x000A;### Downloading openGauss&#x000A;&#x000A;You can download openGauss-server and openGauss-third_party from open source community.&#x000A;&#x000A;https://opengauss.org/zh/&#x000A;&#x000A;From the following website, you can obtain the binarylibs we have compiled. Please unzip it and rename to **binarylibs** after you download.&#x000A;&#x000A;https://opengauss.obs.cn-south-1.myhuaweicloud.com/2.1.0/openGauss-third_party_binarylibs.tar.gz&#x000A;&#x000A;&#x000A;Now we have completed openGauss code, for example, we store it in following directories.&#x000A;&#x000A;- /sda/openGauss-server&#x000A;- /sda/binarylibs&#x000A;- /sda/openGauss-third_party&#x000A;&#x000A;### Compiling Third-Party Software&#x000A;&#x000A;Before compiling the openGauss, compile and build the open-source and third-party software on which the openGauss depends. These open-source and third-party software is stored in the openGauss-third_party code repository and usually needs to be built only once. If the open-source software is updated, rebuild the software.&#x000A;&#x000A;You can also directly obtain the output file of the open-source software compilation and build from the **binarylibs** repository.&#x000A;&#x000A;If you want to compile third-party by yourself, please go to openGauss-third_party repository to see details. &#x000A;&#x000A;After the preceding script is executed, the final compilation and build result is stored in the **binarylibs** directory at the same level as **openGauss-third_party**. These files will be used during the compilation of **openGauss-server**.&#x000A;&#x000A;### Compiling by build.sh&#x000A;&#x000A;build.sh in openGauss-server is an important script tool during compilation. It integrates software installation and compilation and product installation package compilation functions to quickly compile and package code.&#x000A;&#x000A;The following table describes the parameters.&#x000A;&#x000A;| Option | Default Value                | Parameter                      | Description                              |&#x000A;| :----- | :--------------------------- | :----------------------------- | :--------------------------------------- |&#x000A;| -h     | Do not use this option.      | -                              | Help menu.                               |&#x000A;| -m     | release                      | [debug \| release \| memcheck] | Selects the target version.              |&#x000A;| -3rd   | ${Code directory}/binarylibs | [binarylibs path]              | Specifies the path of binarylibs. The path must be an absolute path. |&#x000A;| -pkg   | Do not use this option.      | -                              | Compresses the code compilation result into an installation package. |&#x000A;&#x000A;&gt; **NOTICE:** &#x000A;&gt;&#x000A;&gt; 1. **-m [debug | release | memcheck]** indicates that three target versions can be selected:&#x000A;&gt;    - **release**: indicates that the binary program of the release version is generated. During compilation of this version, the GCC high-level optimization option is configured to remove the kernel debugging code. This option is usually used in the generation environment or performance test environment.&#x000A;&gt;    - **debug**: indicates that a binary program of the debug version is generated. During compilation of this version, the kernel code debugging function is added, which is usually used in the development self-test environment.&#x000A;&gt;    - **memcheck**: indicates that a binary program of the memcheck version is generated. During compilation of this version, the ASAN function is added based on the debug version to locate memory problems.&#x000A;&gt; 2. **-3rd [binarylibs path]** is the path of **binarylibs**. By default, **binarylibs** exists in the current code folder. If **binarylibs** is moved to **openGauss-server** or a soft link to **binarylibs** is created in **openGauss-server**, you do not need to specify the parameter. However, if you do so, please note that the file is easy to be deleted by the **git clean** command.&#x000A;&gt; 3. Each option in this script has a default value. The number of options is small and the dependency is simple. Therefore, this script is easy to use. If the required value is different from the default value, set this parameter based on the actual requirements.&#x000A;&#x000A;Now you know the usage of build.sh, so you can compile the openGauss-server by one command with build.sh.&#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh -m [debug | release | memcheck] -3rd [binarylibs path]&#x000A;```&#x000A;&#x000A;For example: &#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh       # Compile openGauss of the release version. The binarylibs or its soft link must exist in the code directory. Otherwise, the operation fails.&#x000A;[user@linux openGauss-server]$ sh build.sh -m debug -3rd /sda/binarylibs    # Compilate openGauss of the debug version using binarylibs we put on /sda/&#x000A;```&#x000A;&#x000A;The software installation path after compilation is **/sda/openGauss-server/dest**.&#x000A;&#x000A;The compiled binary files are stored in **/sda/openGauss-server/dest/bin**.&#x000A;&#x000A;Compilation log: **make_compile.log**&#x000A;&#x000A;&#x000A;&#x000A;### Compiling by Command&#x000A;&#x000A;1. Run the following script to obtain the system version:&#x000A;&#x000A;   ```&#x000A;   [user@linux openGauss-server]$ sh src/get_PlatForm_str.sh&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTICE:** &#x000A;   &gt;&#x000A;   &gt; - The command output indicates the OSs supported by the openGauss. The OSs supported by the openGauss are centos7.6_x86_64 and openeuler_aarch64.&#x000A;   &gt; - If **Failed** or another version is displayed, the openGauss does not support the current operating system.&#x000A;&#x000A;2. Configure environment variables, add **____** based on the code download location, and replace *** with the result obtained in the previous step.&#x000A;&#x000A;   ```&#x000A;   export CODE_BASE=________     # Path of the openGauss-server file&#x000A;   export BINARYLIBS=________    # Path of the binarylibs file&#x000A;   export GAUSSHOME=$CODE_BASE/dest/&#x000A;   export GCC_PATH=$BINARYLIBS/buildtools/***/gcc7.3/&#x000A;   export CC=$GCC_PATH/gcc/bin/gccexport CXX=$GCC_PATH/gcc/bin/g++&#x000A;   export LD_LIBRARY_PATH=$GAUSSHOME/lib:$GCC_PATH/gcc/lib64:$GCC_PATH/isl/lib:$GCC_PATH/mpc/lib/:$GCC_PATH/mpfr/lib/:$GCC_PATH/gmp/lib/:$LD_LIBRARY_PATH&#x000A;   export PATH=$GAUSSHOME/bin:$GCC_PATH/gcc/bin:$PATH&#x000A;&#x000A;   ```&#x000A;&#x000A;3. Select a version and configure it.&#x000A;&#x000A;   **debug** version:&#x000A;&#x000A;   ```&#x000A;   ./configure --gcc-version=7.3.0 CC=g++ CFLAGS='-O0' --prefix=$GAUSSHOME --3rd=$BINARYLIBS --enable-debug --enable-cassert --enable-thread-safety --without-readline --without-zlib&#x000A;   ```&#x000A;&#x000A;   **release** version:&#x000A;&#x000A;   ```&#x000A;   ./configure --gcc-version=7.3.0 CC=g++ CFLAGS=&quot;-O2 -g3&quot; --prefix=$GAUSSHOME --3rd=$BINARYLIBS --enable-thread-safety --without-readline --without-zlib&#x000A;   ```&#x000A;&#x000A;   **memcheck** version:&#x000A;&#x000A;   ```&#x000A;   ./configure --gcc-version=7.3.0 CC=g++ CFLAGS='-O0' --prefix=$GAUSSHOME --3rd=$BINARYLIBS --enable-debug --enable-cassert --enable-thread-safety --without-readline --without-zlib --enable-memory-check&#x000A;   ```&#x000A;&#x000A;   &gt; **NOTICE:** &#x000A;   &gt;&#x000A;   &gt; 1. *[debug | release | memcheck]* indicates that three target versions are available. &#x000A;   &gt; 2. On the ARM-based platform, **-D__USE_NUMA** needs to be added to **CFLAGS**.&#x000A;   &gt; 3. On the **ARMv8.1** platform or a later version (for example, Kunpeng 920), **-D__ARM_LSE** needs to be added to **CFLAGS**.&#x000A;   &gt; 4. If **binarylibs** is moved to **openGauss-server** or a soft link to **binarylibs** is created in **openGauss-server**, you do not need to specify the **--3rd** parameter. However, if you do so, please note that the file is easy to be deleted by the `git clean` command.&#x000A;   &gt; 5. To build with mysql_fdw, add **--enable-mysql-fdw** when configure. Note that before build mysql_fdw, MariaDB's C client library is needed.&#x000A;   &gt; 6. To build with oracle_fdw, add **--enable-oracle-fdw** when configure. Note that before build oracle_fdw, Oracle's C client library is needed.&#x000A;&#x000A;4. Run the following commands to compile openGauss:&#x000A;&#x000A;   ```&#x000A;   [user@linux openGauss-server]$ make -sj&#x000A;   [user@linux openGauss-server]$ make install -sj&#x000A;   ```&#x000A;&#x000A;5. If the following information is displayed, the compilation and installation are successful:&#x000A;&#x000A;   ```&#x000A;   openGauss installation complete.&#x000A;   ```&#x000A;&#x000A;   The software installation path after compilation is **$GAUSSHOME**.&#x000A;&#x000A;   The compiled binary files are stored in **$GAUSSHOME/bin**.&#x000A;&#x000A;&#x000A;&#x000A;### Compiling the Installation Package &#x000A;&#x000A;Please read the chapter **Compiling by build.sh** first to understand the usage of build.sh and how to compile openGauss by using the script.&#x000A;&#x000A;Now you can compile the installation package with just adding a option `-pkg`.&#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh -m [debug | release | memcheck] -3rd [binarylibs path] -pkg&#x000A;```&#x000A;&#x000A;For example:&#x000A;&#x000A;```&#x000A;[user@linux openGauss-server]$ sh build.sh -pkg      # Compile openGauss installation package of the release version. The binarylibs or its soft link must exist in the code directory. Otherwise, the operation fails.&#x000A;[user@linux openGauss-server]$ sh build.sh -m debug -3rd /sda/binarylibs -pkg   # Compile openGauss installation package of the debug version using binarylibs we put on /sda/&#x000A;```&#x000A;&#x000A;The generated installation package is stored in the **./package** directory.&#x000A;&#x000A;Compilation log: **make_compile.log**&#x000A;&#x000A;Installation package packaging log: **./package/make_package.log**&#x000A;&#x000A;## Quick Start&#x000A;&#x000A;See the [Quick Start](https://opengauss.org/zh/docs/2.1.0/docs/Quickstart/Quickstart.html) to implement the image classification.&#x000A;&#x000A;## Docs&#x000A;&#x000A;For more details about the installation guide, tutorials, and APIs, please see the [User Documentation](https://gitcode.com/opengauss/docs).&#x000A;&#x000A;## Community&#x000A;&#x000A;### Governance&#x000A;&#x000A;Check out how openGauss implements open governance [works](https://gitcode.com/opengauss/community/blob/master/governance.md).&#x000A;&#x000A;### Communication&#x000A;&#x000A;- WeLink- Communication platform for developers.&#x000A;- IRC channel at `#opengauss-meeting` (only for meeting minutes logging purpose)&#x000A;- Mailing-list: &lt;https://opengauss.org/zh/community/onlineCommunication/&gt;&#x000A;&#x000A;## Contribution&#x000A;&#x000A;Welcome contributions. See our [Contributor](https://opengauss.org/en/contribution/) for more details.&#x000A;&#x000A;## Release Notes&#x000A;&#x000A;For the release notes, see our [RELEASE](https://opengauss.org/zh/docs/2.1.0/docs/Releasenotes/Releasenotes.html).&#x000A;&#x000A;## License&#x000A;&#x000A;[MulanPSL-2.0](http://license.coscl.org.cn/MulanPSL2)</textarea>&#x000A;<div class='loader-wrapper'>&#x000A;<div class='ui inline mini active loader'></div>&#x000A;</div></blob-markdown-renderer>&#x000A;</div>
<div class='file_line'></div>

<div class='tree_progress'>
<div class='ui active inverted dimmer'>
<div class='ui small text loader'>Loading...</div>
</div>
</div>
</div>
</div>
<div class='ui small modal' id='modal-linejump'>
<div class='ui custom form content'>
<div class='field'>
<div class='ui right action input'>
<input placeholder='Jump to line...' type='number'>
<div class='ui orange button'>
Go
</div>
</div>
</div>
</div>
</div>
<script>
  $(function() {
    var $fileTitle = $('.file_title');
    var $fixedDiv = $('.file_breadcrumb_wrapper');
    function checkFileTitleTop() {
      if (!$fileTitle.length) return;
      var rect = $fileTitle[0].getBoundingClientRect();
      if (rect.top <= 46) {
        $fixedDiv.show();
        var $fileCatalog = $('.file_catalog')
        if($fileCatalog.length){
          const h = Math.ceil($fileTitle.height())
          $fileCatalog.css('top', `${46+h}px`);
        }
  
      } else {
        $fixedDiv.hide();
      }
    }
    $(window).on('scroll', window.globalUtils.throttle(checkFileTitleTop,100));
    checkFileTitleTop();
  });
</script>

<div class='complaint'>
<div class='ui modal small form' id='landing-comments-complaint-modal'>
<i class='iconfont icon-close close'></i>
<div class='header'>
Report
</div>
<div class='content'>
<div class='appeal-success-tip hide'>
<i class='iconfont icon-ic_msg_success'></i>
<div class='appeal-success-text'>
Report success
</div>
<span>
We will send you the feedback within 2 working days through the letter!
</span>
</div>
<div class='appeal-tip'>
Please fill in the reason for the report carefully. Provide as detailed a description as possible.
</div>
<div class='ui form appeal-form'>
<div class='inline field'>
<label class='left-part appeal-type-wrap'>
Type
</label>
<div class='ui dropdown selection' id='appeal-comments-types'>
<div class='text default'>
Please select a report type
</div>
<i class='dropdown icon'></i>
<div class='menu'></div>
</div>
</div>
<div class='inline field'>
<label class='left-part'>
Reason
</label>
<textarea class='appeal-reason' id='appeal-comment-reason' name='msg' placeholder='Please explain the reason for the report' rows='3'></textarea>
</div>
<div class='ui message callback-msg hide'></div>
<div class='ui small error text message exceeded-size-tip'></div>
</div>
</div>
<div class='actions'>
<div class='ui button blank cancel'>
Cancel
</div>
<div class='ui orange icon button disabled ok' id='complaint-comment-confirm'>
Send
</div>
</div>
</div>
<script>
  var $complaintCommentsModal = $('#landing-comments-complaint-modal'),
      $complainCommentType = $complaintCommentsModal.find('#appeal-comments-types'),
      $complaintModalTip = $complaintCommentsModal.find('.callback-msg'),
      $complaintCommentsContent = $complaintCommentsModal.find('.appeal-reason'),
      $complaintCommentBtn = $complaintCommentsModal.find('#complaint-comment-confirm'),
      complaintSending = false,
      initedCommentsType = false;
  
  function initCommentsTypeList() {
    if (!initedCommentsType) {
      $.ajax({
        url: "/appeals/fetch_types",
        method: 'get',
        data: {'type': 'comment'},
        success: function (data) {
          var result = '';
          for (var i = 0; i < data.length; i++) {
            result = result + "<div class='item' data-value='" + data[i].id + "'>" + data[i].name + "</div>";
          }
          $complainCommentType.find('.menu').html(result);
        }
      });
      $complainCommentType.dropdown({showOnFocus: false});
      initedCommentsType = true;
    }
  }
  $complainCommentType.on('click', function() {
    $complaintCommentsModal.modal({
      autofocus: false,
      onApprove: function() {
        return false;
      },
      onHidden: function() {
        restoreCommonentDefault();
      }
    }).modal('show');
  });
  
  $complaintCommentsContent.on('change keyup', function(e) {
    var content = $(this).val();
    if ($.trim(content).length > 0 && $complainCommentType.dropdown('get value').length > 0 ) {
      $complaintCommentBtn.removeClass('disabled');
      return;
    }
    $complaintCommentBtn.addClass('disabled');
  });
  
  
  $complainCommentType.dropdown({
    showOnFocus: false,
    onChange: function(value, text, $selectedItem) {
      if (value.length > 0 && $.trim($complaintCommentsContent.val()).length > 0) {
        $complaintCommentBtn.removeClass('disabled');
        return
      }
      $complaintCommentBtn.addClass('disabled');
    }
  });
  
  function restoreCommonentDefault() {
    $complainCommentType.dropdown('restore defaults');
    $complaintCommentsContent.val('');
    $('.exceeded-size-tip').text('').hide();
    $complaintModalTip.text('').hide();
    setTimeout(function() {
      setCommentSendTip(false);
    }, 1500);
  }
  
  $complaintCommentBtn.on('click',function(e){
    var reason = $complaintCommentsContent.val();
    var appealableId = $('#landing-comments-complaint-modal').attr('data-id');
    if (complaintSending) {
      return;
    }
    var appealType = $complainCommentType.dropdown('get value');
    var formData = new FormData();
    formData.append('appeal_type_id', appealType);
    formData.append('reason', reason);
    formData.append('appeal_type','Note');
    formData.append('target_id',appealableId);
    $.ajax({
      type: 'POST',
      url: "/appeals",
      cache: false,
      contentType: false,
      processData: false,
      data: formData,
      beforeSend: function() {
        setCommentSendStatus(true);
      },
      success: function(res) {
        if (res.status == 200) {
          setCommentSendTip(true);
          setTimeout(function() {
            $complaintCommentsModal.modal('hide');
            restoreCommonentDefault();
          }, 3000);
        }
        setCommentSendStatus(false);
      },
      error: function(err) {
        showCommonTips(err.responseJSON.message, 'error');
        setCommentSendStatus(false);
      }
    })
  });
  
  function showCommonTips(text, type) {
    $complaintModalTip.text(text).show();
    if (type == 'error') {
      $complaintModalTip.removeClass('success').addClass('error');
    } else {
      $complaintModalTip.removeClass('error').addClass('success');
    }
  }
  
  function setCommentSendStatus(value) {
    complaintSending = value;
    if (complaintSending) {
      $complaintCommentBtn.addClass('loading');
      $complaintCommentsContent.attr('readonly', true);
      $complainCommentType.attr('readonly', true);
    } else {
      $complaintCommentBtn.removeClass('loading');
      $complaintCommentsContent.attr('readonly', false);
      $complainCommentType.attr('readonly', false);
    }
  }
  
  function setCommentSendTip(value) {
    if (value) {
      $('.appeal-success-tip').removeClass('hide');
      $('.appeal-tip').addClass('hide');
      $('.appeal-form').addClass('hide');
      $('#landing-comments-complaint-modal .actions').addClass('hide');
    } else {
      $('.appeal-success-tip').addClass('hide');
      $('.appeal-tip').removeClass('hide');
      $('.appeal-form').removeClass('hide');
      $('#landing-comments-complaint-modal .actions').removeClass('hide');
    }
  }
</script>

<div class='ui small modal' id='misjudgment_appeal_modal'>
<i class='close icon'></i>
<div class='header dividing ui'>
误判申诉
</div>
<div class='content'>
<p>此处可能存在不合适展示的内容，页面不予展示。您可通过相关编辑功能自查并修改。</p>
<p>如您确认内容无涉及 不当用语 / 纯广告导流 / 暴力 / 低俗色情 / 侵权 / 盗版 / 虚假 / 无价值内容或违法国家有关法律法规的内容，可点击提交进行申诉，我们将尽快为您处理。</p>
<div class='buttons'>
<div class='ui button blank cancel'>取消</div>
<div class='ui button orange submit'>提交</div>
</div>
</div>
</div>
<style>
  #misjudgment_appeal_modal .buttons {
    float: right;
    margin-top: 30px;
    margin-bottom: 20px; }
    #misjudgment_appeal_modal .buttons .cancel {
      margin-right: 20px; }
</style>
<script>
  var $misjudgmentAppealModal = $('#misjudgment_appeal_modal');
  $('.cancel').on('click',function(){
    $misjudgmentAppealModal.modal('hide');
  });
  var $jsSubmitAppeal = $misjudgmentAppealModal.find('.submit')
  $jsSubmitAppeal.on('click', function(e) {
    e.preventDefault();
    $(this).addClass('loading').addClass('disabled');
    var type = $(this).attr('data-type');
    var id = $(this).attr('data-id');
    var projectId = $(this).attr('data-project-id');
    var appealType = $(this).attr('data-appeal-type');
    $.ajax({
      type: "PUT",
      url: "/misjudgment_appeal",
      data: {
        type: type,
        id: id,
        project_id: projectId,
        appeal_type: appealType
      },
      success: function(data) {
        Flash.info('提交成功');
        $jsSubmitAppeal.removeClass('loading');
        $misjudgmentAppealModal.modal('hide');
        location.reload()
      },
      error: function(e) {
        Flash.error('提交失败:'+e.responseText);
        $jsSubmitAppeal.removeClass('loading').removeClass('disabled');
        location.reload()
      }
    });
  })
</script>

</div>
<script>
  "use strict";
  $('.js-check-star').checkbox('set unchecked')
</script>

</div>
</div>
</div>
<div class='four wide column' style='display: none;'>
<div class='project__right-side'>
<div class='side-item intro'>
<div class='header'>
<h4>About</h4>
</div>
<div class='content'>
<span class='git-project-desc-text'>openGauss kernel ~ openGauss is an open source relational database management system.</span>
<a class='hide spread' href='javascript:void(0);'>
expand
<i class='caret down icon'></i>
</a>
<a class='retract hide' href='javascript:void(0);'>
collapse
<i class='caret up icon'></i>
</a>
<div class='intro-list'>
<div class='blank d-flex d-flex-between dropdown item js-project-label_show label-list-line-feed project-label-list ui' data-labels='[]' data-url='/opengauss/openGauss-server/update_description'>
<div class='mixed-label'>
</div>

<div class='default'>No labels</div>
</div>
<div class='hide item'>
<i class='iconfont icon-link'></i>
<span class='git-project-homepage'>
<a rel="nofollow" id="homepage" target="_blank" href="/opengauss/openGauss-server/blob/master/README.en.md">/opengauss/openGauss-server/blob/master/README.en.md</a>
</span>
</div>
<div class='item box-licence'>
<i class='iconfont icon-licence'></i>
<span class='license-popup license-clickable' data-license-filename='License' data-license-index='0' data-license-name='MulanPSL-2.0' id='license-popup-0'>
MulanPSL-2.0
</span>
<div class='ui popup dark'>Use MulanPSL-2.0</div>
</div>
<!-- - page = @project.page -->
<!-- - if page&.status? -->
<!-- .item -->
<!-- %i.iconfont.icon-giteepage -->
<!-- Pages： -->
<!-- = link_to page.domain_url, page.domain_url, target: '_blank' -->
<div class='item star-item'>
<i class='iconfont icon-star'></i>
<a class="action-social-count " title="1493" href="/opengauss/openGauss-server/stargazers"><span class='text-bold'>
1.5K
</span>
Stars
</a></div>
<div class='item watch-item'>
<i class='iconfont icon-watch'></i>
<a class="action-social-count" title="444" href="/opengauss/openGauss-server/watchers"><span class='text-bold'>
444
</span>
Watching
</a></div>
<div class='item'>
<i class='iconfont icon-fork'></i>
<a class="action-social-count disabled-style" title="1813" href="/opengauss/openGauss-server/members"><span class='text-bold'>
1.8K
</span>
Forks
</a></div>
</div>
</div>
<div class='content intro-form'>
<div class='ui small input'>
<textarea name='project[description]' placeholder='Description' rows='5'></textarea>
</div>
<div class='ui small input'>
<input data-regex-value='(^$)|(^(http|https):\/\/(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]).*)|(^(http|https):\/\/[a-zA-Z0-9]+([_\-\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,10}(:[0-9]{1,10})?(\?.*)?(\/.*)?$)' name='project[homepage]' placeholder='Homepage(eg: https://gitee.com)' type='text'>
</div>
<button class='ui orange button mt-1 btn-save'>
Save
</button>
<div class='ui blank button btn-cancel-edit'>
Cancel
</div>
</div>
</div>
<div class='side-item release'>
<div class='header'>
<h4>
Releases
<span class='text-muted'>
(10)
</span>
</h4>
<a class="ui link button pull-right" href="/opengauss/openGauss-server/releases">All</a>
</div>
<div class='content ml-3'>
<i class='iconfont icon-release'></i>
<div class='desc'>
<a href="/opengauss/openGauss-server/releases/tag/v6.0.0">6.0.0</a>
</div>
<span class='timeago' datetime='2024-10-14 16:21' title='2024-10-14 16:21:11 +0800'></span>
</div>
</div>
<div class='side-item compass'>
<div class='header mb-1 d-align-center'>
<h4 class='limit-length compass-label mr-1'></h4>
<a class="ui link button compass-qa" href="https://compass.gitee.com/docs/dimensions-define"><i class='iconfont icon-help-circle'></i>
</a></div>
<div class='content'>
<div class='compass-echart-container'>
<div data-url='/opengauss/openGauss-server/compass/chart_data' id='compass-metrics'>
<div class='wrap'></div>
<div class='ui popup radar-popup'>
<h4 class='title'>The Open Source Evaluation Index is derived from the OSS Compass evaluation system, which evaluates projects around the following three dimensions</h4>
<div class='project-radar-list'>
<div class='descript-contianer'>
<div class='descript-title'>
<p class='mb-1'>1. Open source ecosystem</p>
<ul class='mb-1 mt-1'>
<li>Productivity: To evaluate the ability of open-source projects to output software artifacts and open-source value.</li>
<li>Innovation: Used to evaluate the degree of diversity of open source software and its ecosystem.</li>
<li>Robustness: Used to evaluate the ability of open-source projects to resist internal and external interference and self recover in the face of changing development environments.</li>
</ul>
<p>2. Collaboration, People, Software</p>
<ul>
<li>Collaboration: represents the degree and depth of collaboration in open source development behavior.</li>
<li>Observe the influence of core personnel in open source projects, and examine the evaluations of users and developers on open source projects from a third-party perspective.</li>
<li>Software: Evaluate the value of products exported from open-source projects and their ultimate destination. It is also a concrete manifestation of &quot;open source software&quot;, one of the oldest mainstream directions in open source evaluation.</li>
</ul>
<p>3. Evaluation model</p>
<ul>
Based on the dimensions of &quot;open source ecosystem&quot; and &quot;collaboration, people, and software&quot;, identify quantifiable indicators directly or indirectly related to this goal, quantitatively evaluate the health and ecology of open source projects, and ultimately form an open source evaluation index.
</ul>
</div>
</div>
</div>
<div class='finaltime'></div>
</div>
<div class='legend-box ml-1'>
<div class='dimension d-flex'></div>
<div class='compass-type d-flex'></div>
</div>
</div>
</div>
<script src="/static/javascripts/echarts.min.js"></script>
<script src="/static/javascripts/echarts-gl.min.js"></script>
<script src="https://cn-assets.gitee.com/assets/skill_radar/rep_compass_chart-a170f1ecfff8cd448229c0a3b82b074a.js"></script>

</div>
</div>
<div class='side-item contrib' data-url='/opengauss/openGauss-server/contributors_count?ref=master' id='contributor'>
<div class='header'>
<h4>
Contributors
<span class='text-muted' id='contributor-count'></span>
</h4>
<a class="ui link button pull-right" href="/opengauss/openGauss-server/contributors?ref=master">All</a>
</div>
<div class='content' id='contributor-list'></div>
<div class='ui active centered inline loader' id='contributor-loader'></div>
</div>
<div class='side-item' id='languages'>
<div class='header'>
<h4>
Language(Optional)
</h4>
</div>
<div class='content'>
<div class='lang-bar-container mb-2'>
<div class='lang-bar'>
<div class='bar' style='width: 82.0%;background:#f34b7d'></div>
<div class='bar' style='width: 8.2%;background:#555555'></div>
<div class='bar' style='width: 2.9%;background:#336790'></div>
<div class='bar' style='width: 2.7%;background:#4B6C4B'></div>
<div class='bar' style='width: 1.2%;background:#89e051'></div>
<div class='bar' style='width: 3.0%;background:#EDEDED'></div>
</div>
</div>
<div class='lang-legend'>
<span class='d-align-center'>
<span class='lang-dot' style='background:#f34b7d'></span>
<a class="lang-text" href="/explore/all?lang=C%2B%2B">C++</a>
<a class="percentage ml-1 text-muted" href="/explore/all?lang=C%2B%2B">82.0%</a>
</span>
<span class='d-align-center'>
<span class='lang-dot' style='background:#555555'></span>
<a class="lang-text" href="/explore/all?lang=C">C</a>
<a class="percentage ml-1 text-muted" href="/explore/all?lang=C">8.2%</a>
</span>
<span class='d-align-center'>
<span class='lang-dot' style='background:#336790'></span>
<a class="lang-text" href="/explore/all?lang=PLpgSQL">PLpgSQL</a>
<a class="percentage ml-1 text-muted" href="/explore/all?lang=PLpgSQL">2.9%</a>
</span>
<span class='d-align-center'>
<span class='lang-dot' style='background:#4B6C4B'></span>
<a class="lang-text" href="/explore/all?lang=Yacc">Yacc</a>
<a class="percentage ml-1 text-muted" href="/explore/all?lang=Yacc">2.7%</a>
</span>
<span class='d-align-center'>
<span class='lang-dot' style='background:#89e051'></span>
<a class="lang-text" href="/explore/all?lang=Shell">Shell</a>
<a class="percentage ml-1 text-muted" href="/explore/all?lang=Shell">1.2%</a>
</span>
<span class='d-align-center'>
<span class='lang-dot' style='background:#EDEDED'></span>
<a class="lang-text" href="/explore/all?lang=Other">Other</a>
<a class="percentage ml-1 text-muted" href="/explore/all?lang=Other">3.0%</a>
</span>
</div>
</div>
</div>

<div class='side-item events' data-url='/opengauss/openGauss-server/events.json' id='proj-events'>
<div class='header'>
<h4>Activities</h4>
</div>
<div class='content'>
<div class='ui comments' id='event-list'></div>
<a class="loadmore hide" href="javascript:void(0);">Load More
<i class='icon dropdown'></i>
</a><center>
<div class='text-muted nomore hide'>can not load any more</div>
<div class='ui inline loader active'></div>
</center>
</div>
</div>
</div>
<div class='ui modal tiny' id='edit-project-description'>
<i class='iconfont icon-close close'></i>
<div class='header'>Edit</div>
<div class='content'>
<div class='item mb-2'>
<div class='title label'>About</div>
<div class='ui small input'>
<textarea maxlength='200' name='project[description]' placeholder='Description' rows='5'>openGauss kernel ~ openGauss is an open source relational database management system.</textarea>
</div>
</div>
<div class='item mb-2'>
<div class='title label'>Homepage</div>
<div class='ui small input'>
<input data-regex-value='(^$)|(^(http|https):\/\/(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]).*)|(^(http|https):\/\/[a-zA-Z0-9]+([_\-\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,10}(:[0-9]{1,10})?(\?.*)?(\/.*)?$)' name='project[homepage]' placeholder='Homepage(eg: https://gitee.com)' type='text'>
</div>
</div>
</div>
<div class='actions'>
<button class='ui button blank cancel'>Cancel</button>
<button class='ui button orange btn-save'>Save</button>
</div>
</div>

<style>
  #readme-name,
  .license-popup {
    color: #005980;
    cursor: pointer; }
  
  .license-clickable {
    color: #005980;
    cursor: pointer;
    -webkit-transition: color 0.2s ease;
    transition: color 0.2s ease; }
</style>
<script>
  // 公共函数：平滑滚动到指定的license标题
  function scrollToLicenseTitle(licenseIndex) {
    var container = $('.file_readme_title')[0];
    
    if (!container) return;
    
    if (licenseIndex === undefined || licenseIndex === null) {
      // 如果没有licenseIndex，滚动到最左侧
      container.scrollTo({
        left: 0,
        behavior: 'smooth'
      });
      return;
    }
    
    var selectedElement = $('#license-title-' + licenseIndex)[0];
    
    if (selectedElement) {
      // 计算目标位置（元素相对于容器的位置）
      var containerRect = container.getBoundingClientRect();
      var elementRect = selectedElement.getBoundingClientRect();
      var scrollLeft = container.scrollLeft;
      var targetScrollLeft = scrollLeft + (elementRect.left - containerRect.left) - 20; // 留20px边距
      
      // 平滑滚动到目标位置
      container.scrollTo({
        left: targetScrollLeft,
        behavior: 'smooth'
      });
    }
  }
  
  function scrollToReadmeBox() {
    var readmeBox = document.getElementById('git-readme');
    if (readmeBox) {
      const topPos = readmeBox.offsetTop;
      window.scrollTo({ top: topPos, behavior: "smooth" });
    }
  }
  
  window.gon.projectRightSide = {
    homepage: null,
    description: "openGauss kernel ~ openGauss is an open source relational database management system.",
    url: '/opengauss/openGauss-server/update_description',
    i18n: {
      invalidHomepage: 'Invalid homepage',
      descriptionLimitExceeded: 'The length of the about shall not exceed %{limit} characters',
      noDescription: 'no description',
      noPermission: 'no permission',
      requestError: 'update error!'
    }
  }
  window.gon.cloneArrSelectedLabel = [] || []
  $(function () {
    var $editModal = $('#edit-project-description')
    $editModal.modal({
      onShow: function () {
        window.globalUtils.getFocus($editModal.find('textarea'))
      }
    })
    $('.project__right-side').on('click', '.header .btn-edit', function () {
      $editModal.modal('show')
    })
    $('.license-popup').popup({ position: 'bottom center', lastResort: 'bottom center' })
  
    // 处理每个license的点击事件
    $('.license-clickable').click(function(event) {
      event.preventDefault();
      event.stopPropagation();
      
      var licenseName = $(this).data('license-name');
      var licenseIndex = $(this).data('license-index');
      var licenseFilename = $(this).data('license-filename');
      
      // 如果license文件名是README.md，则跳转到readme tab
      if (licenseFilename === 'README.md') {
        // 显示readme内容区域
        $('.readme-content').show()
        $('.readme-edit').show()
        $('.lisence-content').hide()
        $('.lisence-edit').hide()
        
        // 移除所有license标题的active-title类，然后为readme标题添加active-title类
        $('.file_title_license').removeClass('active-title');
        $('.file_title_readme').addClass('active-title');
        
        // 滚动到最左侧
        scrollToLicenseTitle();
      } else {
        // 显示license内容区域
        $('.lisence-edit').hide()
        $('.readme-content').hide()
        $('.readme-edit').hide()
        
        // 移除所有license标题的active-title类，然后为对应的标题添加active-title类
        $('.file_title_license').removeClass('active-title');
        $('#license-title-' + licenseIndex).addClass('active-title');
        $('.file_title_readme').removeClass('active-title');
        
        // 隐藏所有license内容，然后只显示选中的license内容
        $('.lisence-content').hide()
        $('#license-content-' + licenseIndex).show();
        $('#license-edit-' + licenseIndex).show();
        
        // 平滑滚动到对应的license标题
        scrollToLicenseTitle(licenseIndex);
      }
      
      scrollToReadmeBox()
    });
    
    $(".box-readme").click(function(event) {
      $('.lisence-content').hide()
      $('.lisence-edit').hide()
      $('.readme-content').show()
      $('.readme-edit').show()
      $('.file_title_license').removeClass('active-title')
      $('.file_title_readme').addClass('active-title')
      scrollToLicenseTitle()
      scrollToReadmeBox()
    });
  
    $('.js-project-label_show').projectLabel({
      i18n: {
        empty: "The name cannot be empty",
        verify: "10. The name is only allowed to contain Chinese, letters, numbers or a dash (-), cannot start with a dash, and the length is less than 35 characters",
        max: "Select up to 5"
      }
    })
  })
</script>

</div>
<div class='project-right-side-contaner' id='code-parsing'>
<div class='d-flex-between mb-2'>
<div class='title fs-16 d-align-center'>
<img class='mr-1' height='32' src='/static/images/mjc_icon@2x.png' width='32'>
<span class='ai-file-name'>马建仓 AI 助手</span>
</div>
<div>
<i class='iconfont icon-close close gitee-icon-close'></i>
</div>
</div>
<div class='code-parsing-content'>
<div class='sub_title'></div>
<div class='markdown-body'></div>
<div class='bottom-content'>
<div class='js-code-parsing-img'></div>
<div class='ai_code_btns_simple'>
<div class='ai_code_btns_simple_container'>
<div class='mr-1 test-more'>尝试更多</div>
<div class='btn_box' data-content='帮我解读代码' data-text='代码解读' data-value='code_explain'>
<div class='btn_box_title'>代码解读</div>
</div>
<div class='btn_box' data-content='帮我代码找茬' data-text='代码找茬' data-value='code_review'>
<div class='btn_box_title'>代码找茬</div>
</div>
<div class='btn_box' data-content='帮我优化代码' data-text='代码优化' data-value='code_improve'>
<div class='btn_box_title'>代码优化</div>
</div>
</div>
</div>
</div>
</div>
<div class='skeleton'>
<div class='line line1'></div>
<div class='line line2'></div>
<div class='line line3'></div>
<div class='line line4'></div>
<div class='line line1'></div>
<div class='line line2'></div>
<div class='line line3'></div>
<div class='line line4'></div>
<div class='line line1'></div>
<div class='line line2'></div>
<div class='line line3'></div>
<div class='line line4'></div>
</div>
<div class='resize-handle'>
<div class='resize-handle-line'></div>
</div>
<script src="/static/javascripts/markdown-it.min.js"></script>
<script src="https://cn-assets.gitee.com/assets/ai_code_parsing/app-f83eb69e2ecd107b1a533333dea1f4eb.js"></script>
<script>
  $(function() {
    var maxWidthPercentage = 0.5;
    $("#code-parsing").resizable({
      handles: 'e, w', // 通过左边调整大小
      minWidth: 350, // 设置 代码解析框 的最小宽度
      resize: function(event, ui) {
        var parentWidth = $(this).parent().width();
        var newWidthDiv2 = ui.size.width;
        var newWidthDiv1 = parentWidth - newWidthDiv2;
        // 计算最大宽度
        var maxWidthDiv2 = parentWidth * maxWidthPercentage;
        // 确保 代码解析框 不超过最大宽度
        newWidthDiv2 = Math.min(newWidthDiv2, maxWidthDiv2);
        // 确保 文件详情 至少有最小宽度
        newWidthDiv1 = Math.max(parentWidth - newWidthDiv2, 750);
  
        var percentageCode = (newWidthDiv2 / parentWidth) * 100;
        var percentageProject = (newWidthDiv1 / parentWidth) * 100;
  
        $('#code-parsing').css('width',percentageCode+"%")
        $('.git-project-content-wrapper').find('#sixteen').attr('style', 'width: ' + percentageProject + '% !important;');
        $('.right-wrapper').attr('style', 'width: ' + percentageProject + '% !important;');
        $('.project-conter-container').attr('style', 'width: ' + percentageProject + '% !important;');
      }
    });
  })
</script>

</div>
</div>
</div>
<script>
  (function() {
    $(function() {
      Tree.init();
      return TreeCommentActions.init();
    });
  
  }).call(this);
</script>
<script>
  function scrollToReadmeBox() {
    var readmeBox = document.getElementById('git-readme');
    if (readmeBox) {
      const topPos = readmeBox.offsetTop;
      window.scrollTo({ top: topPos, behavior: "smooth" });
    }
  }
  
  $(".box-readme").click(function(event) {
    $('.lisence-content').hide()
    $('.lisence-edit').hide()
    $('.readme-content').show()
    $('.readme-edit').show()
    $('.file_title_license').removeClass('active-title')
    $('.file_title_readme').addClass('active-title')
    scrollToReadmeBox()
  });
  
  // 防止二次挂载
  if (true) {
    window.gon.tree_left_side_loaded = true;
  }
</script>
<link rel="stylesheet" media="all" href="https://cn-assets.gitee.com/assets/markdown_preview-001478f1b12f2725f1b1f76f36b9ce4e.css" />
<script src="https://cn-assets.gitee.com/assets/markdown_preview-f27882a3071270404229ef70dcf6ac7f.js"></script>
<script src="https://cn-assets.gitee.com/webpacks/markdown_render-5627847188396ebb0629.bundle.js" defer="defer"></script>

</div>
<script>
  (function() {
    var donateModal;
  
    Gitee.modalHelper = new GiteeModalHelper({
      alertText: '提示',
      okText: '确定'
    });
  
    donateModal = new ProjectDonateModal({
      el: '#project-donate-modal',
      alipayUrl: '/opengauss/openGauss-server/alipay',
      wepayUrl: '/opengauss/openGauss-server/wepay',
      nameIsBlank: 'name cannot be blank',
      nameTooLong: 'name is too long (maximum is 36 character)',
      modalHelper: Gitee.modalHelper
    });
  
    if (null === 'true') {
      donateModal.show();
    }
  
    $('#project-donate').on('click', function() {
      return donateModal.show();
    });
  
  }).call(this);
</script>
<script>
  Tree.initHighlightTheme('white')
</script>


</div>
<div class='gitee-project-extension'>
<div class='extension lang'>C++</div>
<div class='extension public'>1</div>
<div class='extension https'>https://gitee.com/opengauss/openGauss-server.git</div>
<div class='extension ssh'>git@gitee.com:opengauss/openGauss-server.git</div>
<div class='extension namespace'>opengauss</div>
<div class='extension repo'>openGauss-server</div>
<div class='extension name'>openGauss-server</div>
<div class='extension branch'>master</div>
</div>

<script>
  $(function() {
    GitLab.GfmAutoComplete.dataSource = "/opengauss/openGauss-server/autocomplete_sources"
    GitLab.GfmAutoComplete.Emoji.assetBase = '/assets/emoji'
    GitLab.GfmAutoComplete.setup();
  });
</script>

<footer id='git-footer-main'>
<div class='ui container'>
<div class='logo-row'>
<a href="https://gitee.com"><img alt='Gitee — A Git-based Code Hosting and Research Collaboration Platform' class='logo-img logo-light' src='/static/images/logo-black.svg?t=158106666'>
<img alt='Gitee — A Git-based Code Hosting and Research Collaboration Platform' class='logo-img logo-dark' src='/static/images/logo-white-next.svg?t=158106666'>
</a></div>
<div class='name-important'>
©OSCHINA. All rights reserved
</div>
<div class='ui two column grid d-flex-centeris-en'>
<div class='eight wide column git-footer-left'>
<div class='ui four column grid' id='footer-left'>
<div class='column'>
<div class='ui link list'>
<div class='item'>
<a class="item" href="/all-about-git">Git Resources</a>
</div>
<div class='item'>
<a class="item" rel="nofollow" href="https://help.gitee.com/learn-Git-Branching/">Learning Git</a>
</div>
<div class='item'>
<a class="item" rel="nofollow" href="https://copycat.gitee.com/">CopyCat</a>
</div>
<div class='item'>
<a class="item" href="/appclient">Downloads</a>
</div>
</div>
</div>
<div class='column'>
<div class='ui link list'>
<div class='item'>
<a class="item" href="/gitee-stars">Gitee Stars</a>
</div>
<div class='item'>
<a class="item" href="/gvp">Featured Projects</a>
</div>
<div class='item'>
<a class="item" rel="nofollow" href="https://blog.gitee.com/">Blog</a>
</div>
<div class='item'>
<a class="item" href="/enterprises#nonprofit-plan">Nonprofit</a>
</div>
<div class='item'>
<a class="item" href="https://gitee.com/features/gitee-go">Gitee Go</a>
</div>
</div>
</div>
<div class='column'>
<div class='ui link list'>
<div class='item'>
<a class="item" href="/api/v5/swagger">OpenAPI</a>
</div>
<div class='item'>
<a class="item" href="https://gitee.com/oschina/mcp-gitee">MCP Server</a>
</div>
<div class='item'>
<a class="item" href="https://help.gitee.com">Help Center</a>
</div>
<div class='item'>
<a class="item" href="/self_services">Self-services</a>
</div>
<div class='item'>
<a class="item" href="/help/articles/4378">Updates</a>
</div>
</div>
</div>
<div class='column'>
<div class='ui link list'>
<div class='item'>
<a class="item" href="/about_us">About Us</a>
</div>
<div class='item'>
<a class="item" rel="nofollow" href=" https://gitee.com/oschina/jobs">Join us</a>
</div>
<div class='item'>
<a class="item" href="/terms">Terms of use</a>
</div>
<div class='item'>
<a class="item" href="/oschina/git-osc/issues">Feedback</a>
</div>
<div class='item'>
<a class="item" href="/links.html">Partners</a>
</div>
</div>
</div>
</div>
</div>
<div class='eight wide column right aligned followus git-footer-right'>
<div class='qrcode mr-1'>
<div class='qrcode-box'>
<img alt="Exchange" src="https://cn-assets.gitee.com/assets/communication_QR-3b8de44bedfd3cf6c52c96b1a05771c6.png" />
</div>
<p class='mt-1 mini_app-text'>Exchange</p>
</div>
<div class='qrcode'>
<div class='qrcode-box'>
<img alt="微信服务号" class="weixin-qr" src="https://cn-assets.gitee.com/assets/weixin_QR-853f852365876b5f318023e95cbbfdb6.png" />
</div>
<p class='mt-1 weixin-text'>WeChat</p>
</div>
<div class='phone-and-qq column'>
<div class='ui list official-support-container'>
<div class='item'></div>
<div class='item mail-and-zhihu'>
<a class="icon-popup" title="E-mail" rel="nofollow" href="mailto: client@oschina.cn"><i class='iconfont icon-msg-mail'></i>
<span id='git-footer-email'>client#oschina.cn</span>
</a></div>
<div class='item tel'>
<a class='icon-popup' title='Contact'>
<i class='iconfont icon-tel'></i>
<span>Enterprise:400-606-0201</span>
</a>
</div>
<div class='item tel'>
<a class='d-flex icon-popup' title='Contact'>
<i class='iconfont icon-tel mt-05 mr-05'></i>
<span>Pro：</span>
<div>
赖经理 13058176526
</div>
</a>
</div>
</div>
</div>
</div>
</div>
</div>
<div class='bottombar'>
<div class='ui container'>
<div class='ui d-flex d-flex-between'>
<div class='seven wide column partner d-flex'>
<div class='open-atom d-flex-center'>
<img class="logo-openatom mr-1" alt="开放原子开源基金会" src="https://cn-assets.gitee.com/assets/logo-openatom-new-955174a984c899d2e230d052bdc237cf.svg" />
<a target="_blank" rel="nofollow" href="https://www.openatom.org/">OpenAtom Foundation</a>
<div class='sub-title ml-1'>Cooperative code hosting platform</div>
</div>
<div class='report-12377 d-flex-center ml-3'>
<img class="report-12377__logo mr-1" alt="违法和不良信息举报中心" src="https://cn-assets.gitee.com/assets/12377@2x-1aa42ed2d2256f82a61ecf57be1ec244.png" />
<a target="_blank" rel="nofollow" href="https://www.12377.cn">违法和不良信息举报中心</a>
</div>
<div class='copyright ml-3'>
<a rel="nofollow" href="http://beian.miit.gov.cn/">京ICP备2025119063号</a>
</div>
<div class='beian d-flex-center ml-2'>
<img class="report-12377__logo ml-1" alt="京公网安备11011502039387号" src="https://cn-assets.gitee.com/assets/beian-30b2e25c5da148efae50f89073b26816.png" />
<a target="_blank" rel="nofollow" href="https://beian.miit.gov.cn/">京公网安备11011502039387号</a>
</div>
</div>
<div class='nine wide column right aligned'>
<i class='icon world'></i>
<a href="/language/zh-CN">简 体</a>
/
<a href="/language/zh-TW">繁 體</a>
/
<a href="/language/en">English</a>
</div>
</div>
</div>
</div>
</footer>

<script>
  var officialEmail = $('#git-footer-email').text()
  $('#git-footer-main .icon-popup').popup({ position: 'bottom center' })
  $('#git-footer-email').text(officialEmail.replace('#', '@'))
  window.gon.popover_card_locale = {
    follow:"Follow",
    unfollow:"Following",
    gvp_title: "GVP - Gitee Most Valuable Project",
    project: "The author of ",
    org: "The member of ",
    member: "",
    author: "",
    user_blocked: "This account has been blocked or destroyed",
    net_error: "Network error ",
    unknown_exception: "Unknown exception"
  }
  window.gon.select_message = {
    placeholder: "Please enter Gitee Profile Address or email address"
  }
</script>
<script src="https://cn-assets.gitee.com/webpacks/popover_card-9afe4ce3f1b03daa4ed4.bundle.js"></script>
<link rel="stylesheet" media="all" href="https://cn-assets.gitee.com/webpacks/css/gitee_nps-ae0dbee40f6ddc72015a.css" />
<script src="https://cn-assets.gitee.com/webpacks/gitee_nps-03ff804099144a49b055.bundle.js"></script>
<script src="https://cn-assets.gitee.com/webpacks/gitee_icons-c083090a7801eb0b2ce7.bundle.js"></script>



<div class='side-toolbar'>
<div class='button toolbar-help'>
<i class='iconfont icon-help'></i>
</div>
<div class='ui popup left center dark'>Going to Help Center</div>
<div class='toolbar-help-dialog'>
<div class='toolbar-dialog-header'>
<h3 class='toolbar-dialog-title'>Search</h3>
<form class="toolbar-help-search-form" action="/help/load_keywords_data" accept-charset="UTF-8" method="get"><input name="utf8" type="hidden" value="&#x2713;" />
<div class='ui icon input fluid toolbar-help-search'>
<input name='keywords' placeholder='Please enter a question' type='text'>
<i class='icon search'></i>
</div>
</form>

<i class='iconfont icon-close toolbar-dialog-close-icon'></i>
</div>
<div class='toolbar-dialog-content'>
<div class='toolbar-help-hot-search'>
<div class='toolbar-roll'>
<a class="init active" title="Git 命令在线学习" href="https://help.gitee.com/learn-git-branching/?utm_source==gitee-help-widget"><i class='Blue icon icon-command iconfont'></i>
<span>Git 命令在线学习</span>
</a><a class="init " title="如何在 Gitee 导入 GitHub 仓库" href="https://gitee.com/help/articles/4261?utm_source==gitee-help-widget"><i class='icon icon-clipboard iconfont orange'></i>
<span>如何在 Gitee 导入 GitHub 仓库</span>
</a></div>
<div class='toolbar-list'>
<div class='toolbar-list-item'>
<a href="/help/articles/4114">Git 仓库基础操作</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4166">企业版和社区版功能对比</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4191">SSH 公钥设置</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4194">如何处理代码冲突</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4232">仓库体积过大，如何减小？</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4279">如何找回被删除的仓库数据</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4283">Gitee 产品配额说明</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4284">GitHub仓库快速导入Gitee及同步更新</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4328">什么是 Release（发行版）</a>
</div>
<div class='toolbar-list-item'>
<a href="/help/articles/4354">将 PHP 项目自动发布到 packagist.org</a>
</div>
</div>
</div>
<div class='toolbar-help-search-reseult'></div>
</div>
</div>
<script>
  var opt = { position: 'left center'};
  var $helpSideToolbar = $('.button.toolbar-help');
  var $toolbarRoll = $('.toolbar-roll');
  
  $(function() {
    if (false) {
      $helpSideToolbar.popup(opt).popup({lastResort:'left center'})
    } else {
      $helpSideToolbar.popup({lastResort:'left center'}).popup('show', opt);
      setTimeout(function() {
        $helpSideToolbar.popup('hide', opt);
      }, 3000);
    }
  
    if ($toolbarRoll.length) {
      setInterval(function() {
        var $nextActiveLink = $toolbarRoll.find('a.active').next();
        if (!$nextActiveLink.length) {
          $nextActiveLink = $toolbarRoll.find('a:first-child');
        }
        $nextActiveLink.attr('class', 'active').siblings().removeClass('active init');
      }, 5000);
    }
  })
</script>

<div class='toolbar-appeal popup button'>
<i class='iconfont icon-report'></i>
</div>
<div class='ui popup dark'>
Repository Report
</div>
<script>
  $('.toolbar-appeal').popup({ position: 'left center' });
</script>

<div class='button gotop popup' id='gotop'>
<i class='iconfont icon-top'></i>
</div>
<div class='ui popup dark'>Back to the top</div>
</div>
<div class='form modal normal-modal tiny ui' id='unlanding-complaint-modal'>
<i class='iconfont icon-close close'></i>
<div class='header'>
Login prompt
</div>
<div class='container actions'>
<div class='content'>
This operation requires login to the code cloud account. Please log in before operating.
</div>
<div class='ui orange icon large button ok'>
Go to login
</div>
<div class='ui button blank cancel'>
No account. Register
</div>
</div>
</div>
<script>
  var $elm = $('.toolbar-appeal');
  
  $elm.on('click', function() {
    var modals = $("#unlanding-complaint-modal.normal-modal");
    if (modals.length > 1) {
      modals.eq(0).modal('show');
    } else {
      modals.modal('show');
    }
  })
  $("#unlanding-complaint-modal.normal-modal").modal({
    onDeny: function() {
      window.location.href = "/signup?from=";
    },
    onApprove: function() {
      window.location.href = "/login?from=";
    }
  })
</script>

<style>
  .side-toolbar .bdsharebuttonbox a {
    font-size: 24px;
    color: white !important;
    opacity: 0.9;
    margin: 6px 6px 0px 6px;
    background-image: none;
    text-indent: 0;
    height: auto;
    width: auto;
  }
</style>
<style>
  #udesk_btn a {
    margin: 0px 20px 167px 0px !important;
  }
</style>
<script>
  (function() {
    $('#project-user-message').popup({
      position: 'left center'
    });
  
  }).call(this);
</script>
<script>
  Gitee.initSideToolbar({})
</script>





<script>
  (function() {
    this.__gac = {
      domain: 'www.oschina.net'
    };
  
  }).call(this);
</script>

<script src="https://cn-assets.gitee.com/assets/bdstatic/app-070a9e339ac82bf2bf7ef20375cd4121.js"></script>
<script src="https://hm.baidu.com/hm.js?69c6a9a806f562f1fa028b5b883f3fe3" async="async"></script>
<script src="https://cn-assets.gitee.com/webpacks/build_status-6c0a8a19b67c23fdc7fe.bundle.js"></script>
<script src="https://cn-assets.gitee.com/webpacks/scan_status-129dc7c4b730f50d9d38.bundle.js"></script>
<script src="https://cn-assets.gitee.com/webpacks/mermaid_render-e708d712dc28da655877.bundle.js"></script>
<script src="https://cn-assets.gitee.com/webpacks/check_runs-2af5d367832761b64630.bundle.js"></script>
</body>
</html>
