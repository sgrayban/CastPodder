<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<!--                                                       -->
<!--          CastPodder project                           -->
<!--          ==========================================   -->
<!--          programming: Scott Grayban                   -->
<!--          programming: Andrew Grumet                   -->
<!--          GUI/design:                                  -->
<!--          Content Strategist:                          -->
<!--          Based on the idea of Adam Curry & Dave Winer -->
<!--                                                       -->
<!-- $Id: thank_you.php 324 2006-07-18 21:44:28Z sgrayban $ -->
<!--                                                       -->
  <head>
    <title>CastPodder - A Linux podcast agregrator</title>

  <?php require("../includes/metatags.php");?>
  </head>
  </head>
  <body>
    <table cellpadding="0" cellspacing="0" border="0" width="100%">
      <tbody>
        <tr>
          <td class="column_left" valign="top" align="right">
            <!-- left side -->
            <div class="navigation">
              <?php require("../includes/menu.php");?>
              <br />
              <br />
              <?php require("../includes/developers.php");?>
              <br />
              <br />
              <?php require("../includes/resources.php");?>
            </div>
          </td>
          <td width="50%" valign="top" align="center">
            <!-- body -->
            <center>
              <br>
              <br>
              <img src="/images/splashscreen.png">
              <br>
               CastPodder&reg;&trade; is a Registered Trademark
              <br>
               CastPodder&reg;&trade; is Copyright &copy; 2005-2006 CastPodder Team
              <br>
              <br>
              <b><font size="3">Thank you for donating to CastPodder.
	      <br>Your contributions will help keep the project alive.</font></b>
              <br>
              <br>
               You can return to project forum <a href="http://forum.castpodder.net/">here</a>.
            </center>
            <!-- End main content -->
            <br>
            <br>
             The CastPodder Team
            <hr>
            <a href="http://www.castpodder.net" title="Get CastPodder"><img src="/images/CastPodder_button.png" alt="Get CastPodder"></a> &nbsp;&nbsp;&nbsp;<a href="http://borgforge.net" title="BorgForge Developer"> <img src="/images/bflogo.png" width="124px" height="32px" border="0" alt="BorgForge Developer Logo"></a>
          </td>
          <td class="column_right" valign="top" align="left">
            <!-- right side -->
	<?php require("../includes/news.php");?>
          </td>
        </tr>
        <tr>
          <td class="footer" rowSpan="1" colspan="3" valign="top" align="center">
            <!-- footer -->

	<?php require("../includes/footer.php");?>
          </td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
