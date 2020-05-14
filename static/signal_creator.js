counter = 0;
token_length=0;
value = '';
$(function(){

    $(".error").hide();
    $("#spinner").hide();
    $("#signal_display_container").hide();
    $("#make_signal").click(function(){
        $(".error").hide();
        $("#spinner").hide();
        $("#signal_display_container").hide();
        var signal = $("input#signal").val();
        value = signal;
        if (signal == ''){
            $('label#signal_error').show();
            $('input#signal').focus();
            return false;
        }
        $("#input_signal").hide();
        display_signal(signal);
    });

    $('#addrow').click(function(){
        add_row(token_length);
    });

    $("#signal_table").on("click", ".ibtnDel", function (event) {
        $(this).closest("tr").remove();
        counter -= 1;
    });

    $("#send_data").click(function(){
        var threshold = $("input#threshold").val();
        if (threshold == ''){
            $('label#threshold_error').show();
            $('input#threshold').focus();
            return false;
        }
        var return_obj=send_table_data();
        return_obj['threshold']=threshold;
        return_obj['value']=value;
        return_obj['prod_id']=$("input#prod_id").val();
        $("#spinner").show();
        $('#spinner').focus();
        var URL = "http://0.0.0.0:8080/signal_creator?json_data="+JSON.stringify(return_obj)
        $.get(URL,function(data,status){
            $("#spinner").hide();
            alert("Data saved");
        });
        return false;
    });
    return false;
});

function display_signal(signal){
    $('#signal_display_container').show();
    $('#col1').text(signal);
    var URL = "http://0.0.0.0:8080/sentence_processor?signal="+signal;
    $.get(URL,function(response,status){
        var all_data = JSON.parse(response);
        var data = all_data["data"];
        console.log(data)
        var max_len = all_data["max_len"];
        var html = '<tr>'
        for(var i=0;i<data.length;i++){
            for(key in data[i]){
                token_length++;
                html=html+'<td>'+key+'<br/><input type="text" value="1" size="1" placeholder="weight"/></td>';
            }
        }
        html=html+'</tr>';
        $("#signal_table tbody").append(html);

        for(var check_len=0;check_len<max_len;check_len++)
        {
            var html="<tr>";
            for(var i=0;i<data.length;i++){
                if (data[i][Object.keys(data[i])[0]] != ""){
                    html+="<td><input type='text' class='form-control'  value="+data[i][Object.keys(data[i])[0]][check_len]+"></input></td>"
                }
                else{
                    html+="<td><input type='text' class='form-control'/></td>"
                }
            }
            html=html+'<td><input type="button" class="ibtnDel btn btn-md btn-danger "  value="Delete"></td>';
            html+="/tr";
            $("#signal_table tbody").append(html);
        }
    });

}

function add_row(token_length){
    var html = '<tr>';
    for(var i=0;i<token_length;i++){
        html=html+'<td><input type="text" class="form-control" /></td>';
    }
    html=html+'<td><input type="button" class="ibtnDel btn btn-md btn-danger "  value="Delete"></td>';
    $("#signal_table tbody").append(html);
    counter++;
}

function send_table_data(){
    var dict={};
    var scores=[];
    var first_row=true;
    var x=1;
    $('#signal_table tr').each(function(){
        var y=1;
        $.each(this.cells,function(){
            if (first_row){
                if ($(this).text() !='\n'){
                    dict["tok_".concat(x.toString())]=[$(this).text()];
                    $inputs=$(this).find('input');
                    if ($inputs.val() == ''){
                        alert('Please input the weights');
                        $(this).focus();
                        return false;
                    }
                    else{
                        scores.push($inputs.val());
                    }
                    x++;
                }
            }
            else{
                $inputs=$(this).find("input");
                if ($inputs.attr('type') != 'button'){
                    if ($inputs.val() != ''){
                        dict['tok_'.concat(y.toString())].push($inputs.val());
                    }
                }
                y++;
            }
        });
        first_row=false;
    });
    return {"dict":dict,"scores":scores};
}