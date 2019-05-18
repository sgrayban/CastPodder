<!--								-->
<!-- $Id: rss-feed.php 178 2005-11-24 10:06:50Z sgrayban $	-->
<!--								-->
<table>
  <tbody>
    <tr>
      <td>
      <u><div class="header"><b>Latest Blog</b></div></u>
    </td>
  </tr>
<?php
include_once "rss_fetch.php";
$url = "http://blog.borgnet.us/?feed=rss2";  //RSS Feed to parse
$show = 5;   //Show the latest x headlines
$update = 1;  //Dont update if its older
$html  = "  <tr>\n";
$html .= "    <td>\n";
$html .= "      <font size='+1'>\n";
$html .= "      <a href='#{link}' target='_new'>#{title}</a></font><br />\n";
$html .= "      #{description}<br />\n";
$html .= "      <font size='2'>#{pubDate}<br /><br />\n";
$html .= "    </td>\n";
$html .= "  </tr>\n";
$rss = new rss_parser($url, $show, $html, $update);
?>
</table>
