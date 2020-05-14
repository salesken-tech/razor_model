$(function(){
    var url = '';
    $(".error").hide();
    $("#spinner").hide();
    $("#result_table").hide();
    $("#match").click(function(){
        $("#spinner").hide();
        $(".error").hide();
        $("#result_table").hide();
        var sentence = $("#sentence").val();
        var org_id = $("#org_id").val();
        if (sentence == '' && org_id == ''){
            $('.error').show();
            $(".error").focus();
            return false;
        }
        if (org_id == ''){
            var data_string = "sentence="+sentence;
            $.ajax({
            type : "POST",
            url : "http://35.244.25.4:8080/sentence_match",
            data : data_string,
            success : function(response,status) {
                if (response.length > 0){
                    console.log(response);
                    markup="";
                    for (i = 0; i < response.length; i++){
                        markup+="<tr>\n"+
                            "<td>"+response[i].input_sentence+"</td>\n"+
                            "<td>"+response[i].signal+"</td>\n"+
//                            "<td><div class='andy'>"+response[i].tokens+"</div><div style='display:none;'>"+response[i].html_+"</div></td>\n"+
                            "<td>"+response[i].tokens+"</td>\n"+
                            "<td>"+response[i].score+"</td>\n"+
                            "<td>"+response[i].threshold+"</td>\n"+
                            "<td>"+response[i].id+"</td>\n"+
                            "</tr>";
                    }
                    $(".table tbody").append(markup);
                    $("#result_table").show();
                }
                else{
                    alert("No match found");
                    location.reload(true);
                }


                }
            });
        }else{
            $("#spinner").show();
            $("#spinner").focus();
            var data_string = "task_id="+org_id;
            $.ajax({
            type : "POST",
            url : "http://35.244.25.4:8080/lead_qualification_razor?"+data_string,
            success : function(response,status) {
                if (response.length > 0){
                    markup="";
                    for (i = 0; i < response.length; i++){
                        markup+="<tr>\n"+
                            "<td>"+response[i].input_sentence+"</td>\n"+
                            "<td>"+response[i].signal+"</td>\n"+
                            "<td>"+response[i].tokens+"</td>\n"+
                            "<td>"+response[i].score+"</td>\n"+
                            "<td>"+response[i].threshold+"</td>\n"+
                            "<td>"+response[i].id+"</td>\n"+
                            "</tr>";
                    }
                    $(".table tbody").append(markup);
                    $("#spinner").hide();
                    $("#result_table").show();
                }
                else{
                    alert("No match found");
                    location.reload(true);
                }
                }
            });
        }
    });
    return false;
});