<?php

@require("./ip_in_range.php");

$headers = apache_request_headers();

$ip = "";
if (@$headers["X-Forwarded-For"]) {
	    $ips = explode(",",$headers["X-Forwarded-For"]);
	        $ip  = $ips[0];
} else {
	    $ip = $_SERVER['REMOTE_ADDR'];
}

//https://api.github.com/meta
$range = "172.0.0.0/8";
if (ipv4_in_range($ip, $range)) {
	echo "IP ".$ip." in range";
} else {
	header('HTTP/1.1 403 Forbidden');
	echo "<body>\n";
        echo "<span style=\"color: #ff0000\">IP not allowed to trigger deploy</span>\n"; 
        echo "</body>\n</html>";
        exit;
}

print_r($_POST);
?>
