let cstate = -1;
let cpage = ['home','wallet','transaction','mine','nodes']; //wallet,mine
let baseUrl = 'http://localhost:10000'
// create tips
let tip = document.createElement('div');
tip.id = 'tip';
function tips(data,duration=800) {
    let style = {
        boxShadow:"5px 5px 10px blueviolet",
        borderRadius:"5px",
        backgroundColor:"gray",
        color:'white',
        position:"absolute",
        zIndex:10,
        width:'400px',
        height:'100px',
        top:"50%",
        left:"50%",
        textAlign:'center',
        lineHeight:'80px',
        transform:"translate(-50%,-50%)"
    }
    for(let i in style)
        tip.style[i] = style[i];
    if(document.getElementById('tip') == null){
        document.body.appendChild(tip);
        tip.innerHTML = data;
        setTimeout("document.body.removeChild(tip)" ,duration);
    }
}


//change pages
$('.page').slideUp('0');
$('#choice').find('li').hover(function(){
    let choice_state =  $(this).attr('id')[$(this).attr('id').length-1];
    if(cstate != choice_state){
    // last hide
    $('#choice'+cstate).css('opacity',0.6);
    $('#'+cpage[cstate]).slideUp('50');
    cstate = choice_state;
    // current show
    $('#choice'+cstate).css('opacity',1)
    $('#'+cpage[cstate]).slideDown('200'); // this one
    }
})

let province = null;
let city = null;

$.ajax({
    url: 'http://api.map.baidu.com/location/ip?ak=ia6HfFL660Bvh43exmH9LrI6',
    type: 'POST',
    dataType: 'jsonp',
    success:function(data) {
        province = data.content.address_detail.province;
        city = data.content.address_detail.city;
    }
})

let private_addr = null;
let private_key = null;
let address = null;
let amount = null;


//home
function getAddress(){
    $.get(baseUrl+'/address/get',function(data,status) {
        if(status == 'success'){
            address = data.address
            $('#homeAddress').html(address)
            $('#transactionSenderAddress').children('textarea').val(address);
        }else{
            tips('GET ADDRESS ERROR');
        }
    })
}
function getAmount(){
    $.get(baseUrl+'/amount/get',function(data,status){
        if(status=='success'){
            amount = Number(data.amount);
            $('#homeAmount').html(amount)
        }else{
            tips('GET AMOUNT ERROR')
        }
    })
}
getAddress()
getAmount()
let clipboard = new ClipboardJS('#homeAddressCopy',{text:function(){return address}});
clipboard.on('success',function(){
    tips('address copied',800);
})
$('#homeAmountRenew').click(function(){
    getAmount();
})


// wallet page
// copy function instantiate
function copyFromPrev(text){
    let textarea = $(this).prev();
    textarea.select();
    document.execCommand("Copy");
    tips(text,800);
}
$('#walletPublicKey').children('button').click({'text':'public key is copied'},copyFromPrev)
$('#walletPrivateKey').children('button').click({'text':'private key is copied'},copyFromPrev)
// submit wallet generator get private key
$('#wallet').children('button').click(function(){
    $.get(baseUrl+'/wallet/new',function(data,status){
        if(status == 'success'){
            private_key = data.private_key
            console.log('fuck')
            $('#walletPublicKey').children('textarea').html(data.public_key);
            $('#walletPrivateKey').children('textarea').html(data.private_key);
            console.log('wtf');
            console.log($('#transactionSenderPrivateKey').children('textarea'));
            $('#transactionSenderPrivateKey').children('textarea').html(data.private_key);
            tips(data.message,1000);
        }else{
            tips('WALLET CREATE ERROR');
        }
    });
})

// transaction page
$('#transaction').children('button').click(function(){

    senderAddress = $('#transactionSenderAddress').children('textarea').val();
    senderPrivateKey=$('#transactionSenderPrivateKey').children('textarea').val();
    recipientAddress=$('#transactionRecipientAddress').children('textarea').val();
    value=$('#transactionAmount').children('textarea').val();

    values = Number(values)

    if(value>amount){
        tips("you don't have enough coin");
    }else{
        amount -= value;
    $.post(baseUrl+'/transaction/new',
        {
            senderAddress:senderAddress,
            senderPrivateKey:senderPrivateKey,
            recipientAddress:recipientAddress,
            amount:value
        },
    function(data,status){
        if(status == 'success'){
            tips(data.message,1000);
        }else{
            tips('TRANSACTION CREATE ERROR');
        }
    });}
})

//mine page
function consensusChain(callback){
    $.get(baseUrl+'/nodes/resolve',function(data,status){
        if(status=='success'){
            callback();
        }else{
            tips('resolve Conflict fail',800);
            return False;
        }
    })
}
function mine(){
    $.get(baseUrl+'/mine',function(data, status){
        if(status == 'success'){
            
            $('#mineIndex').html('index:'+data.index);
            $('#mineProof').html('proof:'+data.proof);
            $('#minePreviousHash').html('previous_hash:'+data.previous_hash);
            $('#mine').children('div').children().slideDown();
            tips(data.message,800);
        }
    })
}
$('#mine').children('div').children().slideUp()
$('#mine').children('button').click(function(){
    consensusChain(mine);
})

// add nodes
$('#nodes').children('button').click(function(){
    let nodes = $(this).prev().children('textarea').val();
    $.post(baseUrl+'/nodes/register',
        {
            nodes:nodes
        },
        function(data,status){
            tips('nodes added',800);
        }
        )
})