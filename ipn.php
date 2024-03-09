<?php
class CoinPaymentsAPI {
    private $public_key = '616e319dad674f8906f129a735d299d6665388a0fe3f4e075ffc3e2b9c3ce8f3';
    private $private_key = 'D544Edec2fa5725C5913C5806665393ec58769563f5C7477DfBb8A8C4302867b';
    private $ch = null;
    
    public function __construct($public_key, $private_key) {
        $this->public_key = $public_key;
        $this->private_key = $private_key;
        $this->ch = null;
    }

    public function check_payment_status($txn_id) {
        $response = $this->api_call('get_tx_info', array('txid' => $txn_id));

        if (!isset($response['status'])) {
            return 'Invalid response from CoinPayments API.';
        }

        if ($response['status'] == 100) {
            return 'Payment successful!';
        } elseif ($response['status'] < 0) {
            return 'Payment failed.';
        } else {
            return 'Payment is still processing.';
        }
    }

    private function api_call($cmd, $req = array()) {
        if (empty($this->public_key) || empty($this->private_key)) {
            return array('error' => 'You have not set your public and private keys!');
        }

        $req['version'] = 1;
        $req['cmd'] = $cmd;
        $req['key'] = $this->public_key;
        $req['format'] = 'json';

        $post_data = http_build_query($req, '', '&');
        $hmac = hash_hmac('sha512', $post_data, $this->private_key);

        if ($this->ch === null) {
            $this->ch = curl_init('https://www.coinpayments.net/api.php');
            curl_setopt($this->ch, CURLOPT_FAILONERROR, TRUE);
            curl_setopt($this->ch, CURLOPT_RETURNTRANSFER, TRUE);
            curl_setopt($this->ch, CURLOPT_SSL_VERIFYPEER, 0);
        }
        curl_setopt($this->ch, CURLOPT_HTTPHEADER, array('HMAC: '.$hmac));
        curl_setopt($this->ch, CURLOPT_POSTFIELDS, $post_data);

        $data = curl_exec($this->ch);
        if ($data !== FALSE) {
            $dec = json_decode($data, TRUE);
            if ($dec !== NULL && count($dec)) {
                return $dec;
            } else {
                return array('error' => 'Unable to parse JSON result ('.json_last_error().')');
            }
        } else {
            return array('error' => 'cURL error: '.curl_error($this->ch));
        }
    }
}

// Example usage:
$COINPAYMENTS_PUBLIC_KEY = 'YOUR_PUBLIC_KEY';
$COINPAYMENTS_PRIVATE_KEY = 'YOUR_PRIVATE_KEY';
$api = new CoinPaymentsAPI($COINPAYMENTS_PUBLIC_KEY, $COINPAYMENTS_PRIVATE_KEY);

// Transaction ID to check
$txn_id_to_check = 'YOUR_TRANSACTION_ID';

// Check payment status
$result = $api->check_payment_status($txn_id_to_check);

// Output the result
echo $result;
?>
