<!--                                                         -->
<!-- $Id: donations2.php 175 2005-11-24 09:43:56Z sgrayban $ -->
<!--                                                         -->
<!-- donate -->
<div style="border: 1px dotted #33CC33; padding: 10px; width: 118px; text-align: left; font-size:11px;">
<b><div class="header">Donate to CastPodder!</div></b>
Donations will continue to be used wisely in the development of CastPodder. Your support is appreciated - thank you!
<br><br>
It's good karma, and great things will happen to you the rest of your life. :)
<br />
<script type="text/javascript" language="JavaScript">
<!-- Copyright 2003 Bontrager Connection, LLC
// See article "Changing Form Action URLs On-The-Fly" linked 
//    from URL http://willmaster.com/possibilities/archives 
//    for more information about how to use this code.
function ActionDeterminator()
{
if(document.myform.reason[0].checked == true) {
   document.myform.action = '$20';
   }
if(document.myform.reason[1].checked == true) {
   document.myform.action = '$10';
   }
if(document.myform.reason[2].checked == true) {
   document.myform.action = '$5';
   }
if(document.myform.reason[3].checked == true) {
   document.myform.action = '$0';
   }
return true;
}
// -->
</script>
<form name="myform" method="post" action="">
<br>
<input type="radio" name="reason" checked>$20<br>
<input type="radio" name="reason">$10<br>
<input type="radio" name="reason">$5<br>
<input type="radio" name="reason">other<br>
<br>
<input type="submit" value="Donate!" onClick="return ActionDeterminator();"><br>
</form>
</div>
<!-- end donate -->
